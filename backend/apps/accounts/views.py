from django.contrib.auth import get_user_model

# validate_password is called directly here (not as a serializer field
# validator) because password strength has to be judged against the user it
# belongs to — see the long note on the import in serializers.py.
from django.contrib.auth.password_validation import validate_password

# Django's own password-reset token machinery — reused here instead of the
# custom TimestampSigner-based approach in tokens.py (which is only used
# for email verification). default_token_generator produces a token that's
# invalidated automatically if the user's password or last_login changes in
# the meantime, which is exactly the "has this link already been used or
# gone stale" property a password-reset link needs and TimestampSigner
# alone doesn't provide.
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

# force_bytes/force_str convert between str and bytes as needed for
# base64 encoding; urlsafe_base64_encode/decode turn the user's UUID pk into
# a compact, URL-safe token component (and back) for the reset link.
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# ScopedRateThrottle reads a view's `throttle_scope` attribute and looks up
# the matching rate in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
# (settings/base.py) — one throttle class reused across every rate-limited
# view here, each with a different scope string.
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

# OutstandingToken/BlacklistedToken are the DB tables behind
# rest_framework_simplejwt.token_blacklist (INSTALLED_APPS). Every refresh
# token issued is recorded as an OutstandingToken; blacklisting one is what
# makes an otherwise-stateless JWT stop working. Used by the password reset
# flow below to evict sessions.
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

# simplejwt's base views. LoginView and ThrottledTokenRefreshView below
# subclass these purely to attach throttling; the actual token logic is
# entirely inherited.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .emails import send_duplicate_registration_email, send_password_reset_email, send_verification_email
from .serializers import (
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from .tokens import read_verification_token

User = get_user_model()

# The single response body every registration attempt receives, whether it
# created an account or found the address already registered. Defined once,
# as a constant, precisely because the two code paths returning it MUST stay
# byte-identical — if they ever drift apart, the difference between them
# becomes the account-enumeration oracle this design exists to remove.
REGISTRATION_RESPONSE = {"detail": "Registered. Check your email to verify your account."}


class RegisterView(APIView):
    """
    Creates a student account, or silently declines to when the address is
    already registered — the caller cannot tell which happened.

    Registration used to reject a duplicate email with a 400 ("user with
    this email already exists"), courtesy of the UniqueValidator DRF
    attaches to a unique=True model field. That is a user-enumeration
    oracle: anyone could probe this endpoint to discover which email
    addresses have accounts on the platform. The password-reset endpoint
    below goes to real trouble to avoid exactly that leak, and registration
    was quietly undoing it.

    Now both paths return REGISTRATION_RESPONSE with a 201. A new address
    gets an account plus a verification email; an already-registered
    address gets no new account and instead a notification email to its
    real owner telling them an attempt was made (see
    emails.send_duplicate_registration_email). The person submitting the
    form learns nothing either way; the actual account holder is the one
    who finds out.
    """

    # Must be reachable while logged out — overrides the project-wide
    # default of IsAuthenticated (REST_FRAMEWORK settings) since obviously a
    # new user has no token yet at registration time.
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    # Rate-limited to 5/hour per IP (see settings/base.py) — prevents mass
    # fake-account creation. Also bounds how fast the duplicate-notification
    # path above could be used to send mail to an address someone else owns.
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        # raise_exception=True: on validation failure (bad email format,
        # weak password, unchecked legal acknowledgements) DRF automatically
        # returns a 400 with the field errors — no manual error-response
        # branch needed here. Note that "email already taken" is no longer
        # one of those failures; see the class docstring.
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # iexact matches UserManager.create_user's normalize_email behavior,
        # so "A@Example.com" is recognised as the existing "a@example.com"
        # account rather than slipping through to a create that would then
        # fail on the database's unique constraint.
        existing = User.objects.filter(email__iexact=email).first()
        if existing is not None:
            send_duplicate_registration_email(existing)
            return Response(REGISTRATION_RESPONSE, status=status.HTTP_201_CREATED)

        try:
            # .save() calls RegisterSerializer.create(), which routes through
            # User.objects.create_user (hashes the password, defaults
            # is_active=False).
            user = serializer.save()
        except IntegrityError:
            # Lost the race: another request registered this same address
            # between the check above and this insert. The database's
            # unique=True constraint is what actually caught it — that
            # constraint is deliberately still on the model even though the
            # serializer no longer enforces uniqueness, precisely so this
            # case fails safely instead of creating a duplicate account.
            # Answer exactly as the "already registered" branch does, so
            # even this timing window leaks nothing.
            return Response(REGISTRATION_RESPONSE, status=status.HTTP_201_CREATED)

        # Fires immediately, synchronously, in the request/response cycle —
        # fine for now since Resend/console-backend calls are fast, but
        # would be a candidate to move to an async task queue if email
        # sending ever became a bottleneck or unreliable dependency.
        send_verification_email(user)
        return Response(REGISTRATION_RESPONSE, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    # Reachable while logged out — this IS the action that makes an account
    # usable in the first place.
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    # 20/hour per IP. Verification tokens are signed with SECRET_KEY and so
    # aren't realistically guessable; this is a backstop against blind
    # hammering of the endpoint rather than a defence against a credible
    # attack path.
    throttle_scope = "verify_email"

    def get(self, request, token):
        # Decodes + validates the signed token (checks signature AND that
        # it's not older than VERIFICATION_TOKEN_MAX_AGE_SECONDS) — see
        # tokens.py. Returns None for either a forged or an expired token;
        # both cases are handled identically below.
        user_id = read_verification_token(token)
        if user_id is None:
            return Response(
                {"detail": "Invalid or expired verification link."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            # Covers the edge case of a validly-signed token for a user
            # that no longer exists (e.g. account was deleted after the
            # email was sent) — still a 400, just a different underlying
            # cause than an invalid signature.
            return Response({"detail": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        # update_fields=["is_active"] makes this an UPDATE targeting only
        # that one column, rather than rewriting every field on the row —
        # slightly more efficient and avoids accidentally clobbering
        # concurrent changes to unrelated fields.
        user.save(update_fields=["is_active"])
        return Response({"detail": "Email verified. You can now log in."})


class MeView(APIView):
    # Requires a valid access token — this endpoint's entire purpose is to
    # return data about "whoever the token belongs to", so anonymous access
    # doesn't make sense here (this is actually redundant with the
    # project-wide IsAuthenticated default, but stated explicitly for
    # clarity since so many neighboring views override it to AllowAny).
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user is populated by JWTAuthentication (see
        # REST_FRAMEWORK settings) from the Bearer token on the request —
        # no manual lookup needed. MeSerializer exposes only the
        # safe-to-return subset of fields (email/full_name/subscription_status).
        return Response(MeSerializer(request.user).data)


class LoginView(TokenObtainPairView):
    # Everything except throttling is inherited from TokenObtainPairView —
    # it already validates credentials via Django's authenticate() (which
    # checks is_active, so an unverified account is correctly rejected) and
    # returns {access, refresh} tokens on success.
    throttle_classes = [ScopedRateThrottle]
    # 10/min per IP — slows down password-guessing/brute-force attempts
    # without meaningfully affecting a legitimate user who mistypes a
    # password a couple of times.
    throttle_scope = "login"


class ThrottledTokenRefreshView(TokenRefreshView):
    """
    simplejwt's TokenRefreshView with a rate limit attached.

    Subclassed for exactly the same reason as LoginView above: the library
    view's behavior is correct and wanted as-is, it just shipped without
    throttling. Left unbounded, this endpoint is an unauthenticated
    (a refresh token is the only credential) target that mints fresh access
    tokens, so it deserves a ceiling like every other token-issuing path.
    """

    throttle_classes = [ScopedRateThrottle]
    # 60/hour per IP. A legitimate client refreshes a 30-minute access token
    # roughly twice an hour, so this leaves ample headroom for a student
    # using several devices/tabs at once while still bounding abuse.
    throttle_scope = "token_refresh"


class LogoutView(APIView):
    # Must present a valid access token to log out — an anonymous request
    # has no session to end.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Blacklisting (not just discarding client-side) is what makes
            # logout actually revoke access — without this, a copied
            # refresh token would keep working even after the user "logs
            # out", since JWTs are stateless by default. Requires the
            # rest_framework_simplejwt.token_blacklist app (settings) to
            # store the blacklist entry.
            RefreshToken(refresh_token).blacklist()
        except Exception:
            # Broad except is deliberate: RefreshToken(...) can raise
            # several different simplejwt/jwt-library exception types for a
            # malformed, expired, or already-blacklisted token, and the
            # response is identical either way — there's no meaningfully
            # different action the client should take.
            return Response(
                {"detail": "Invalid or already-blacklisted token."}, status=status.HTTP_400_BAD_REQUEST
            )
        # 205 Reset Content: signals "the action succeeded, and the client
        # should reset its state" — appropriate here since the frontend is
        # expected to clear its stored tokens/redirect to login.
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestView(APIView):
    # Reachable while logged out — this is how a user regains access after
    # forgetting their password.
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    # 5/hour per IP — this endpoint sends email to an address supplied by
    # the caller, so it also needs protecting against being used to spam
    # arbitrary inboxes.
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Always respond 200 regardless of whether the email exists, so this
        # endpoint can't be used to enumerate registered accounts.
        # iexact makes the lookup case-insensitive, matching normalize_email's
        # behavior at registration time (see UserManager.create_user).
        #
        # is_active=True mirrors what Django's own PasswordResetForm does.
        # Without it, an account that never completed email verification
        # would be sent a reset link, complete the reset successfully, and
        # then still be unable to log in (authenticate() rejects inactive
        # users) with nothing explaining why. Verifying the email address is
        # the step that unblocks such an account, not resetting its password.
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user is not None:
            # base64-encodes the UUID pk so it can safely live in a URL
            # query string (uid=...) without escaping issues.
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Generated fresh per request; becomes invalid automatically if
            # the user's password changes before it's used (see the
            # default_token_generator import comment above).
            token = default_token_generator.make_token(user)
            send_password_reset_email(user, uid, token)

        return Response({"detail": "If that email is registered, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    # Reachable while logged out — the whole point is recovering access
    # without being logged in.
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    # Separate scope/rate from the request step above, since this endpoint
    # is guessable-token brute-force territory rather than email-spam
    # territory.
    throttle_scope = "password_reset_confirm"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # Reverses the base64 encoding done in
            # PasswordResetRequestView to recover the raw UUID pk string.
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            # Catches both "no such user" and a malformed/corrupted uid that
            # fails to decode into anything resembling a valid pk — both are
            # reported identically as a bad link, since neither is
            # something the user can act on differently.
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, data["token"]):
            # Covers a forged token, an expired one (default timeout ~ a
            # few days per Django's PASSWORD_RESET_TIMEOUT), or one that was
            # already used to reset the password once (which changes the
            # user's password hash, invalidating the token per how
            # default_token_generator derives its hash).
            return Response({"detail": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

        # Strength checking happens here rather than as a serializer field
        # validator because it needs the User — only now, after uid/token
        # have been verified, is it known who this reset is even for.
        # Passing the user is what lets UserAttributeSimilarityValidator
        # reject a new password that is a thin disguise of the account's own
        # email or name. Checked only after the token is verified, so this
        # can't be used as an oracle to probe password rules against an
        # account someone doesn't control.
        try:
            validate_password(data["new_password"], user)
        except DjangoValidationError as exc:
            # Keyed on "new_password" so the body matches the shape a field
            # validator would have produced, which is what the frontend
            # reset form reads.
            raise_errors = {"new_password": list(exc.messages)}
            return Response(raise_errors, status=status.HTTP_400_BAD_REQUEST)

        # set_password hashes the new password before storage — same as
        # registration, never stored/logged in plain text.
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])

        # Evict every existing session for this account.
        #
        # Without this, a password reset changed the password but left every
        # previously-issued refresh token working for its full 14-day
        # lifetime. That defeats the main reason people reset a password in
        # the first place: someone who believes they are compromised resets
        # it, and the attacker holding a stolen refresh token keeps their
        # access anyway.
        #
        # Note what this can and cannot revoke. Refresh tokens are recorded
        # in the database (OutstandingToken) precisely so they CAN be
        # revoked, and blacklisting them is immediate. Already-issued ACCESS
        # tokens are stateless — nothing is stored server-side to invalidate
        # — so an attacker's current access token keeps working until it
        # expires. That window is bounded by SIMPLE_JWT's
        # ACCESS_TOKEN_LIFETIME (30 minutes), which is exactly why that
        # lifetime is kept short. Closing it entirely would mean checking a
        # revocation list on every single API request, trading away the
        # statelessness that makes JWT auth worth using here.
        self._revoke_outstanding_tokens(user)

        return Response({"detail": "Password reset successfully."})

    @staticmethod
    def _revoke_outstanding_tokens(user) -> None:
        """Blacklists every refresh token currently outstanding for `user`."""
        # bulk_create over a loop of BlacklistedToken.objects.create():
        # a user with several devices can have a number of outstanding
        # tokens, and this keeps the whole revocation to one INSERT.
        #
        # ignore_conflicts=True handles tokens that are already blacklisted
        # (from a previous logout, or a rotation) — the row already exists
        # and re-inserting it would violate the one-to-one constraint.
        # Silently skipping those is correct: the desired end state is
        # "blacklisted", and they already are.
        outstanding = OutstandingToken.objects.filter(user=user)
        BlacklistedToken.objects.bulk_create(
            [BlacklistedToken(token=token) for token in outstanding],
            ignore_conflicts=True,
        )
