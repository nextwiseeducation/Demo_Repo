from django.contrib.auth import get_user_model
# Django's own password-reset token machinery — reused here instead of the
# custom TimestampSigner-based approach in tokens.py (which is only used
# for email verification). default_token_generator produces a token that's
# invalidated automatically if the user's password or last_login changes in
# the meantime, which is exactly the "has this link already been used or
# gone stale" property a password-reset link needs and TimestampSigner
# alone doesn't provide.
from django.contrib.auth.tokens import default_token_generator
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
from rest_framework_simplejwt.tokens import RefreshToken
# simplejwt's base view for POST /login/ — handles validating
# email+password and returning {access, refresh} tokens. LoginView below
# subclasses it purely to attach throttling; the actual login logic is
# entirely inherited.
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import send_password_reset_email, send_verification_email
from .serializers import (
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from .tokens import read_verification_token

User = get_user_model()


class RegisterView(APIView):
    # Must be reachable while logged out — overrides the project-wide
    # default of IsAuthenticated (REST_FRAMEWORK settings) since obviously a
    # new user has no token yet at registration time.
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"  # rate-limited to 5/hour per IP (see settings/base.py) — prevents mass fake-account creation

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        # raise_exception=True: on validation failure (bad email format,
        # weak password, etc.) DRF automatically returns a 400 with the
        # field errors — no manual error-response branch needed here.
        serializer.is_valid(raise_exception=True)
        # .save() calls RegisterSerializer.create(), which routes through
        # User.objects.create_user (hashes the password, defaults
        # is_active=False).
        user = serializer.save()
        # Fires immediately, synchronously, in the request/response cycle —
        # fine for now since Resend/console-backend calls are fast, but
        # would be a candidate to move to an async task queue if email
        # sending ever became a bottleneck or unreliable dependency.
        send_verification_email(user)
        return Response({"detail": "Registered. Check your email to verify your account."}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]  # reachable while logged out — this IS the action that makes an account usable in the first place

    def get(self, request, token):
        # Decodes + validates the signed token (checks signature AND that
        # it's not older than VERIFICATION_TOKEN_MAX_AGE_SECONDS) — see
        # tokens.py. Returns None for either a forged or an expired token;
        # both cases are handled identically below.
        user_id = read_verification_token(token)
        if user_id is None:
            return Response({"detail": "Invalid or expired verification link."}, status=status.HTTP_400_BAD_REQUEST)

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
    throttle_scope = "login"  # 10/min per IP — slows down password-guessing/brute-force attempts without meaningfully affecting a legitimate user who mistypes a password a couple of times


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # must present a valid access token to log out — an anonymous request has no session to end

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
            return Response({"detail": "Invalid or already-blacklisted token."}, status=status.HTTP_400_BAD_REQUEST)
        # 205 Reset Content: signals "the action succeeded, and the client
        # should reset its state" — appropriate here since the frontend is
        # expected to clear its stored tokens/redirect to login.
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]  # reachable while logged out — this is how a user regains access after forgetting their password
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"  # 5/hour per IP — this endpoint sends email to an address supplied by the caller, so it also needs protecting against being used to spam arbitrary inboxes

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Always respond 200 regardless of whether the email exists, so this
        # endpoint can't be used to enumerate registered accounts.
        # iexact makes the lookup case-insensitive, matching normalize_email's
        # behavior at registration time (see UserManager.create_user).
        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
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
    permission_classes = [AllowAny]  # reachable while logged out — the whole point is recovering access without being logged in
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"  # separate scope/rate from the request step above, since this endpoint is guessable-token brute-force territory rather than email-spam territory

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

        # set_password hashes the new password before storage — same as
        # registration, never stored/logged in plain text.
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password reset successfully."})
