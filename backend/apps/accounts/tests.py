from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator

# django.core.mail.outbox — when EMAIL_BACKEND is Django's test backend
# (automatically substituted during test runs regardless of what
# local.py/production.py configure), every send_mail() call is appended
# here instead of actually being sent — lets tests assert on subject/body
# without a real mail provider.
from django.core import mail

# The default cache backend — used directly in ThrottlingTests because
# DRF's throttle classes store request counts/timestamps in the cache, so
# clearing it is required for throttle tests to start from a clean state
# each run.
from django.core.cache import cache

# reverse() resolves a URL name (e.g. "login", set in urls.py) to its
# actual path — tests use names instead of hardcoded path strings so they
# don't break if a URL path is ever restructured.
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

# APITestCase (DRF's test case) provides self.client as a DRF-aware test
# client (handles JSON request/response bodies, exposes response.data)
# instead of Django's default TestCase's HTML-oriented test client.
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

from .models import UserRole
from .permissions import IsContentAdminOrAbove, IsSuperuser
from .roles import backfill_roles
from .tokens import make_verification_token

User = get_user_model()


def registration_payload(**overrides):
    """
    A complete, valid registration POST body.

    Exists because RegisterSerializer requires `accepted_disclaimer` and
    `accepted_terms` — the server-side gate behind the registration page's
    two legal checkboxes. They were added to the serializer without the
    tests being updated, which turned the whole registration suite red and,
    worse, silently disabled the throttling test below (it died on its
    first assertion, so it stopped exercising the throttle it exists to
    verify). Building the body in one place means a future required field
    breaks one function, not every registration test.
    """
    payload = {
        "email": "student@example.com",
        "password": "a-strong-password-123",
        "full_name": "Jane Student",
        "accepted_disclaimer": True,
        "accepted_terms": True,
    }
    payload.update(overrides)
    return payload


class RegistrationAndVerificationTests(APITestCase):
    def test_register_creates_inactive_user_and_sends_email(self):
        response = self.client.post(
            reverse("register"),
            registration_payload(),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="student@example.com")
        # Confirms registration does NOT immediately activate the account —
        # is_active must stay False until the verification link is used
        # (see VerifyEmailView).
        self.assertFalse(user.is_active)
        # Confirms exactly one email was "sent" (captured in mail.outbox)
        # as a side effect of registering, and that it's plausibly the
        # verification email by checking its subject.
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].subject.lower())

    def test_verify_email_activates_account(self):
        # Creates the user directly via the ORM (bypassing the register
        # endpoint) to isolate this test to just the verification step.
        user = User.objects.create_user(email="student@example.com", password="a-strong-password-123")
        self.assertFalse(user.is_active)

        # Generates a real, currently-valid token the same way
        # send_verification_email would, without needing to parse it out of
        # a sent email.
        token = make_verification_token(user.pk)
        response = self.client.get(reverse("verify-email", args=[token]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # refresh_from_db() re-reads the row from the database — necessary
        # because the in-memory `user` object still holds its pre-request
        # state; the view ran in a separate request/response cycle that
        # mutated the database row, not this Python object.
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_verify_email_rejects_invalid_token(self):
        # A string that was never signed by make_verification_token — the
        # signature check in read_verification_token should fail and the
        # view should respond 400, not 500 or 200.
        response = self.client.get(reverse("verify-email", args=["not-a-real-token"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        # setUp runs before every test method in this class — creates one
        # already-verified user and one still-unverified user so both login
        # paths (success and "blocked pending verification") can be tested
        # without repeating the user-creation boilerplate in each test.
        self.password = "a-strong-password-123"
        self.active_user = User.objects.create_user(
            email="active@example.com", password=self.password, is_active=True
        )
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com", password=self.password, is_active=False
        )

    def test_login_succeeds_for_verified_user(self):
        response = self.client.post(
            reverse("login"), {"email": "active@example.com", "password": self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Confirms the response actually contains both JWTs — a 200 alone
        # wouldn't prove the token payload is shaped correctly.
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejected_for_unverified_user(self):
        # Django's authenticate() checks is_active as part of its default
        # ModelBackend, so this exercises that built-in behavior via
        # TokenObtainPairView rather than any custom code in this project —
        # still worth testing explicitly since it's load-bearing for the
        # "must verify email first" requirement.
        response = self.client.post(
            reverse("login"), {"email": "inactive@example.com", "password": self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    def test_logout_blacklists_refresh_token(self):
        User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", is_active=True
        )
        login_response = self.client.post(
            reverse("login"), {"email": "student@example.com", "password": "a-strong-password-123"}
        )
        access, refresh = login_response.data["access"], login_response.data["refresh"]

        # self.client.credentials(...) sets a header that's attached to
        # every subsequent request made by this client instance — mirrors
        # how the real frontend would attach "Authorization: Bearer
        # <access>" to authenticated requests.
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = self.client.post(reverse("logout"), {"refresh": refresh})
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)

        # The real assertion: after logout, that SAME refresh token must no
        # longer work to obtain a new access token — proves the token was
        # actually blacklisted server-side, not just that the endpoint
        # returned success.
        refresh_response = self.client.post(reverse("token-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com", password="old-password-123", is_active=True
        )

    def test_request_reset_sends_email_for_existing_user(self):
        response = self.client.post(reverse("password-reset"), {"email": "student@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_request_reset_does_not_leak_unknown_email(self):
        # The key security property under test: requesting a reset for an
        # email that ISN'T registered must still return 200 (same as a
        # known email would) — but critically, must NOT send an email,
        # since there's no user to send it to. Both assertions together
        # confirm this endpoint can't be used to probe which emails have
        # accounts (the response alone is identical either way; only this
        # test's visibility into mail.outbox reveals the actual behavior
        # difference).
        response = self.client.post(reverse("password-reset"), {"email": "nobody@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_reset_changes_password(self):
        # Builds a real, valid uid+token pair exactly as
        # PasswordResetRequestView/send_password_reset_email would, so this
        # test exercises the confirm step in isolation.
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "a-new-strong-password-456"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        # check_password re-hashes the given plaintext and compares against
        # the stored hash — the only correct way to verify a password was
        # actually changed (comparing raw hash strings would be fragile and
        # implementation-specific).
        self.assertTrue(self.user.check_password("a-new-strong-password-456"))

    def test_confirm_reset_rejects_bad_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": "bad-token", "new_password": "a-new-strong-password-456"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ThrottlingTests(APITestCase):
    """
    Confirms register/login are actually rate-limited, using a 2/min test
    rate (vs. the real 5/hour and 10/min) so the test stays fast.

    ScopedRateThrottle.THROTTLE_RATES is bound as a class attribute at
    import time (rest_framework/throttling.py), so django.test.override_settings
    on REST_FRAMEWORK does NOT reach it — it has to be patched directly.
    Throttle state also lives in the default cache, which persists across
    tests in the same run unless cleared.
    """

    def setUp(self):
        # Without this, throttle counts left over from a previous test
        # method (or a previous test class) would leak in and cause
        # spurious 429s or false passes, since the cache isn't
        # automatically reset between tests the way the database is.
        cache.clear()
        # Saves the real rates so they can be restored in tearDown — this
        # is a genuine monkeypatch of a shared class attribute, so it must
        # be undone or it would leak into every other test class that runs
        # afterward in the same process.
        self._original_rates = ScopedRateThrottle.THROTTLE_RATES
        ScopedRateThrottle.THROTTLE_RATES = {
            "register": "2/min",
            "login": "2/min",
            "password_reset": "2/min",
            "password_reset_confirm": "2/min",
        }

    def tearDown(self):
        # Runs after every test method in this class, success or failure —
        # restores the class attribute so later-running test classes see
        # the original (unpatched) rates.
        ScopedRateThrottle.THROTTLE_RATES = self._original_rates

    def test_register_throttled_after_limit(self):
        # First 2 requests (the patched limit) should succeed normally —
        # each with a distinct email, since register would otherwise fail
        # for a different reason (duplicate email) that would make this
        # test ambiguous about which behavior is actually being checked.
        for i in range(2):
            response = self.client.post(
                reverse("register"),
                registration_payload(email=f"student{i}@example.com"),
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # The 3rd request, still within the same minute, must be rejected
        # by the throttle before it even reaches the view logic.
        response = self.client.post(
            reverse("register"),
            registration_payload(email="student-over-limit@example.com"),
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_throttled_after_limit(self):
        # Uses a wrong password on every attempt — the throttle is meant to
        # kick in regardless of whether the credentials would have been
        # correct, since its purpose is limiting the *rate* of attempts
        # (e.g. brute-forcing), not just rate-limiting failures for some
        # other reason.
        User.objects.create_user(email="student@example.com", password="wrong-password-guess", is_active=True)

        for _ in range(2):
            response = self.client.post(
                reverse("login"), {"email": "student@example.com", "password": "incorrect"}
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 3rd attempt within the window is throttled (429) rather than
        # evaluated for credential correctness (which would be 401 again).
        response = self.client.post(
            reverse("login"), {"email": "student@example.com", "password": "incorrect"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class MeTests(APITestCase):
    def test_returns_current_user(self):
        User.objects.create_user(
            email="student@example.com",
            password="a-strong-password-123",
            full_name="Jane Student",
            is_active=True,
        )
        login_response = self.client.post(
            reverse("login"), {"email": "student@example.com", "password": "a-strong-password-123"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checks each field MeSerializer is supposed to expose individually,
        # including that subscription_status defaults to "FREE" (the
        # SubscriptionStatus default in models.py) for a brand-new account.
        self.assertEqual(response.data["email"], "student@example.com")
        self.assertEqual(response.data["full_name"], "Jane Student")
        self.assertEqual(response.data["subscription_status"], "FREE")

    def test_requires_authentication(self):
        # No credentials attached to this client — confirms the endpoint
        # can't be called anonymously despite MeView existing at all (guards
        # against someone accidentally weakening permission_classes later).
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegistrationEnumerationTests(APITestCase):
    """
    Registering an address that already has an account must be
    indistinguishable from registering a fresh one.

    Registration previously answered a duplicate with a 400 ("user with
    this email already exists"), which let anyone probe the endpoint to
    learn which addresses have accounts here. That mattered particularly
    because the password-reset endpoint deliberately avoids the same leak
    (see PasswordResetTests.test_request_reset_does_not_leak_unknown_email)
    — one endpoint quietly undid the other's protection.
    """

    def test_duplicate_email_returns_identical_response_to_a_fresh_registration(self):
        # The response to a genuinely new address is the baseline that the
        # duplicate case has to match exactly.
        fresh = self.client.post(reverse("register"), registration_payload(email="new@example.com"))
        self.assertEqual(fresh.status_code, status.HTTP_201_CREATED)

        duplicate = self.client.post(reverse("register"), registration_payload(email="new@example.com"))

        # Both the status code and the body must match. A difference in
        # either one is all an attacker needs to tell the two cases apart,
        # which is the whole vulnerability.
        self.assertEqual(duplicate.status_code, fresh.status_code)
        self.assertEqual(duplicate.data, fresh.data)

    def test_duplicate_email_does_not_create_a_second_account(self):
        self.client.post(reverse("register"), registration_payload(email="taken@example.com"))
        self.client.post(reverse("register"), registration_payload(email="taken@example.com"))

        self.assertEqual(User.objects.filter(email__iexact="taken@example.com").count(), 1)

    def test_duplicate_email_notifies_the_real_owner_instead_of_verifying(self):
        self.client.post(reverse("register"), registration_payload(email="owner@example.com"))
        mail.outbox.clear()

        self.client.post(reverse("register"), registration_payload(email="owner@example.com"))

        # Exactly one email, addressed to the existing account holder —
        # this is the point of the design: the person who submitted the
        # form learns nothing, while the actual owner is told an attempt
        # happened.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        # Must NOT be another verification email: sending one would let an
        # attacker trigger real verification mail for an address they do
        # not control, and would imply a new account had been created.
        self.assertNotIn("verify", mail.outbox[0].subject.lower())

    def test_duplicate_detection_is_case_insensitive(self):
        # UserManager.create_user normalizes the domain part of an address,
        # so a differently-cased duplicate must still be recognised rather
        # than falling through to a create that the database would reject.
        self.client.post(reverse("register"), registration_payload(email="mixed@example.com"))
        response = self.client.post(reverse("register"), registration_payload(email="MIXED@Example.com"))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email__iexact="mixed@example.com").count(), 1)


class PasswordStrengthTests(APITestCase):
    """
    AUTH_PASSWORD_VALIDATORS includes UserAttributeSimilarityValidator,
    which rejects a password that is a lightly-disguised copy of the user's
    own email or name. It only works when validate_password() is handed the
    user — as a bare DRF field validator it received user=None and did
    nothing at all, silently. These tests pin that it is actually wired up.
    """

    def test_registration_rejects_password_similar_to_email(self):
        response = self.client.post(
            reverse("register"),
            registration_payload(email="jane.harrington@example.com", password="jane.harrington"),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Keyed on the field, so the frontend form can show the error
        # against the password input rather than as a form-level message.
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email__iexact="jane.harrington@example.com").exists())

    def test_registration_rejects_common_password(self):
        response = self.client.post(reverse("register"), registration_payload(password="password123"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_reset_confirm_rejects_weak_password(self):
        # A reset must not become a way to set a password weaker than
        # registration would ever have accepted.
        user = User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", is_active=True
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "12345678"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)
        # The old password must still work — a rejected reset must not
        # half-apply.
        user.refresh_from_db()
        self.assertTrue(user.check_password("a-strong-password-123"))


class PasswordResetRevokesSessionsTests(APITestCase):
    """
    Resetting a password must evict existing sessions.

    Otherwise the reset changes the password but leaves every
    previously-issued refresh token valid for its full 14-day lifetime —
    defeating the main reason someone resets a password: they believe they
    are compromised, and the attacker holding a stolen token keeps access.
    """

    def setUp(self):
        self.password = "a-strong-password-123"
        self.user = User.objects.create_user(
            email="student@example.com", password=self.password, is_active=True
        )
        login = self.client.post(
            reverse("login"), {"email": "student@example.com", "password": self.password}
        )
        # This is the token standing in for one an attacker has stolen: it
        # is issued BEFORE the reset and must stop working after it.
        self.stolen_refresh = login.data["refresh"]

    def _reset_password(self, new_password):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        return self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": new_password},
        )

    def test_refresh_token_issued_before_reset_stops_working(self):
        # Proves the precondition: the token is genuinely usable first, so a
        # later failure can only be caused by the reset itself.
        before = self.client.post(reverse("token-refresh"), {"refresh": self.stolen_refresh})
        self.assertEqual(before.status_code, status.HTTP_200_OK)

        self.assertEqual(self._reset_password("an-entirely-different-pw-99").status_code, status.HTTP_200_OK)

        after = self.client.post(reverse("token-refresh"), {"refresh": self.stolen_refresh})
        self.assertEqual(after.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_is_idempotent_against_already_blacklisted_tokens(self):
        # Logging out blacklists that refresh token; the reset then tries to
        # blacklist every outstanding token for the user, including this
        # already-blacklisted one. Without ignore_conflicts on the bulk
        # insert, the duplicate row would raise and turn a successful reset
        # into a 500.
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer {}".format(
                self.client.post(
                    reverse("login"), {"email": "student@example.com", "password": self.password}
                ).data["access"]
            )
        )
        self.client.post(reverse("logout"), {"refresh": self.stolen_refresh})
        self.client.credentials()

        self.assertEqual(self._reset_password("another-good-password-77").status_code, status.HTTP_200_OK)

    def test_new_password_works_after_reset(self):
        # The revocation must not be so eager that it breaks the actual
        # goal of the flow.
        self._reset_password("an-entirely-different-pw-99")

        login = self.client.post(
            reverse("login"), {"email": "student@example.com", "password": "an-entirely-different-pw-99"}
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)


class PasswordResetInactiveAccountTests(APITestCase):
    """
    An account that never completed email verification must not be sent a
    reset link. It would reset successfully and then still be unable to log
    in (authenticate() rejects inactive users) with nothing explaining why —
    verifying the address is what unblocks such an account, not resetting
    its password. Mirrors Django's own PasswordResetForm, which filters
    is_active=True.
    """

    def test_no_email_sent_for_unverified_account(self):
        User.objects.create_user(
            email="unverified@example.com", password="a-strong-password-123", is_active=False
        )

        response = self.client.post(reverse("password-reset"), {"email": "unverified@example.com"})

        # Still the same generic 200 — skipping the send must not become a
        # new way to detect which accounts exist or are verified.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_response_is_identical_for_verified_unverified_and_unknown(self):
        User.objects.create_user(email="active@example.com", password="a-strong-password-123", is_active=True)
        User.objects.create_user(
            email="inactive@example.com", password="a-strong-password-123", is_active=False
        )

        responses = [
            self.client.post(reverse("password-reset"), {"email": address})
            for address in ("active@example.com", "inactive@example.com", "nobody@example.com")
        ]

        # All three must be byte-identical; any divergence is an
        # enumeration oracle.
        self.assertEqual({r.status_code for r in responses}, {status.HTTP_200_OK})
        self.assertEqual(len({str(r.data) for r in responses}), 1)


class RoleDefaultsTests(APITestCase):
    """create_user/create_superuser must set User.role consistently with is_staff/is_superuser."""

    def test_create_user_defaults_to_student_role(self):
        user = User.objects.create_user(email="student@example.com", password="a-strong-password-123")
        self.assertEqual(user.role, UserRole.STUDENT)

    def test_create_superuser_sets_superuser_role(self):
        user = User.objects.create_superuser(email="root@example.com", password="a-strong-password-123")
        self.assertEqual(user.role, UserRole.SUPERUSER)


class BackfillRolesTests(APITestCase):
    """
    apps.accounts.roles.backfill_roles is called directly here (not via a
    migration executor, which Django's test runner makes painful without
    django-test-migrations) — it's a plain function precisely so it can be
    unit-tested this way.
    """

    def test_backfill_maps_superuser_and_staff_flags_to_roles(self):
        superuser = User.objects.create_user(
            email="super@example.com", password="a-strong-password-123", is_superuser=True, is_staff=True
        )
        content_admin = User.objects.create_user(
            email="content@example.com", password="a-strong-password-123", is_staff=True, is_superuser=False
        )
        plain_student = User.objects.create_user(email="plain@example.com", password="a-strong-password-123")

        # Force every row back to the STUDENT default first, simulating the
        # state right after migration 0004 (AddField) has run but before
        # 0005 (the backfill under test) has.
        User.objects.all().update(role=UserRole.STUDENT)

        backfill_roles(User)

        superuser.refresh_from_db()
        content_admin.refresh_from_db()
        plain_student.refresh_from_db()
        self.assertEqual(superuser.role, UserRole.SUPERUSER)
        self.assertEqual(content_admin.role, UserRole.CONTENT_ADMIN)
        self.assertEqual(plain_student.role, UserRole.STUDENT)


class _FakeRequest:
    """Minimal stand-in for a DRF Request — the permission classes under test only read .user."""

    def __init__(self, user):
        self.user = user


class RolePermissionClassTests(APITestCase):
    """
    IsSuperuser/IsContentAdminOrAbove × {anonymous, student, content_admin,
    superuser, inactive}. These gate every apps.admin_api endpoint, so a
    mistake here silently exposes or locks out an entire dashboard section.
    """

    def setUp(self):
        self.student = User.objects.create_user(
            email="student2@example.com", password="a-strong-password-123", is_active=True
        )
        self.content_admin = User.objects.create_user(
            email="content2@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.superuser = User.objects.create_user(
            email="super2@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.SUPERUSER,
        )
        self.inactive_superuser = User.objects.create_user(
            email="inactivesuper@example.com",
            password="a-strong-password-123",
            is_active=False,
            role=UserRole.SUPERUSER,
        )

    def test_is_superuser_permission(self):
        perm = IsSuperuser()
        self.assertFalse(perm.has_permission(_FakeRequest(AnonymousUser()), None))
        self.assertFalse(perm.has_permission(_FakeRequest(self.student), None))
        self.assertFalse(perm.has_permission(_FakeRequest(self.content_admin), None))
        self.assertTrue(perm.has_permission(_FakeRequest(self.superuser), None))
        # is_active=False users still authenticate() to False under
        # Django's normal auth flow, but this permission class only checks
        # role — assert that explicitly rather than assuming it, since
        # request.user.is_authenticated is True for any real (non-Anonymous)
        # User instance regardless of is_active.
        self.assertTrue(perm.has_permission(_FakeRequest(self.inactive_superuser), None))

    def test_is_content_admin_or_above_permission(self):
        perm = IsContentAdminOrAbove()
        self.assertFalse(perm.has_permission(_FakeRequest(AnonymousUser()), None))
        self.assertFalse(perm.has_permission(_FakeRequest(self.student), None))
        self.assertTrue(perm.has_permission(_FakeRequest(self.content_admin), None))
        self.assertTrue(perm.has_permission(_FakeRequest(self.superuser), None))


class MeIncludesRoleTests(APITestCase):
    def test_me_response_includes_role(self):
        User.objects.create_user(
            email="roled@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        login_response = self.client.post(
            reverse("login"), {"email": "roled@example.com", "password": "a-strong-password-123"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "CONTENT_ADMIN")


class LoginTokenRoleClaimTests(APITestCase):
    """The access token issued on login must carry the user's role as a claim."""

    def test_access_token_carries_role_claim(self):
        User.objects.create_user(
            email="claimtest@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.SUPERUSER,
        )
        response = self.client.post(
            reverse("login"), {"email": "claimtest@example.com", "password": "a-strong-password-123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access = AccessToken(response.data["access"])
        self.assertEqual(access["role"], "SUPERUSER")

    def test_role_claim_survives_refresh_rotation(self):
        User.objects.create_user(
            email="rotatetest@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        login_response = self.client.post(
            reverse("login"), {"email": "rotatetest@example.com", "password": "a-strong-password-123"}
        )
        refresh_response = self.client.post(
            reverse("token-refresh"), {"refresh": login_response.data["refresh"]}
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        access = AccessToken(refresh_response.data["access"])
        self.assertEqual(access["role"], "CONTENT_ADMIN")
