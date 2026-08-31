from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    ThrottledTokenRefreshView,
    VerifyEmailView,
)

# Mounted at /api/auth/ by config/urls.py, so e.g. "login/" here becomes
# POST /api/auth/login/. Each `name=` is what reverse()/`{% url %}` and the
# test suite (see tests.py, which uses reverse("login") etc.) refer to
# instead of hardcoding path strings.
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    # <str:token> captures the signed verification token straight from the
    # URL path (as sent in the email link) rather than a query string —
    # matches the emails.py verify_url format's expectation that the
    # frontend extracts the token and calls this endpoint with it.
    path("verify-email/<str:token>/", VerifyEmailView.as_view(), name="verify-email"),
    path("login/", LoginView.as_view(), name="login"),
    # simplejwt's ready-made refresh view (takes a refresh token, returns a
    # new access token — and, per SIMPLE_JWT's ROTATE_REFRESH_TOKENS
    # setting, a new refresh token too), wrapped in views.py only to attach
    # a rate limit. Its token logic is used exactly as the library ships it.
    path("token/refresh/", ThrottledTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
