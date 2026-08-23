from django.contrib.auth import get_user_model
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

from .tokens import make_verification_token

User = get_user_model()


class RegistrationAndVerificationTests(APITestCase):
    def test_register_creates_inactive_user_and_sends_email(self):
        response = self.client.post(
            reverse("register"),
            {"email": "student@example.com", "password": "a-strong-password-123", "full_name": "Jane Student"},
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
        response = self.client.post(reverse("login"), {"email": "active@example.com", "password": self.password})
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
        response = self.client.post(reverse("login"), {"email": "inactive@example.com", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(email="student@example.com", password="a-strong-password-123", is_active=True)
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
        self.user = User.objects.create_user(email="student@example.com", password="old-password-123", is_active=True)

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
                {"email": f"student{i}@example.com", "password": "a-strong-password-123"},
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # The 3rd request, still within the same minute, must be rejected
        # by the throttle before it even reaches the view logic.
        response = self.client.post(
            reverse("register"),
            {"email": "student-over-limit@example.com", "password": "a-strong-password-123"},
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
        response = self.client.post(reverse("login"), {"email": "student@example.com", "password": "incorrect"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class MeTests(APITestCase):
    def test_returns_current_user(self):
        user = User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", full_name="Jane Student", is_active=True
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
