from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole

# First permissions.py in the project — everything before this used stock
# DRF classes (IsAuthenticated/AllowAny) only. These two gate the custom
# admin dashboard (apps.admin_api) and any future endpoint that needs a
# role check should import from here rather than duplicating the logic.


class IsSuperuser(BasePermission):
    """
    Business-analytics-grade access: full platform visibility, including
    revenue figures.

    Deliberately reads user.role from the database (via request.user, which
    JWTAuthentication has already fetched) rather than the JWT's own "role"
    claim. simplejwt copies custom claims onto every access token minted
    from a refresh token, so with ROTATE_REFRESH_TOKENS a role demoted
    server-side would still be sitting in the token for up to
    REFRESH_TOKEN_LIFETIME (14 days) if authorization trusted the claim
    instead of the database.
    """

    message = "This action requires superuser access."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.role == UserRole.SUPERUSER)


class IsContentAdminOrAbove(BasePermission):
    """Content-team access: question bank management and feedback triage, no financials."""

    message = "This action requires content admin access."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in (UserRole.CONTENT_ADMIN, UserRole.SUPERUSER)
        )
