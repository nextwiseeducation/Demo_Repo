from django.contrib import admin
# Django's ready-made admin page for user management (list view, detail
# view with fieldsets, add-user flow) — subclassed below rather than
# reimplemented, since it already handles password hashing display,
# permission widgets, etc. correctly; we only need to point it at our
# custom User/forms instead of Django's defaults.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserChangeForm, UserCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Tells BaseUserAdmin to use our custom forms (see forms.py), which
    # know about the email-based User model, instead of its own defaults
    # built around Django's username-based User.
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    ordering = ("email",)  # BaseUserAdmin defaults to ordering by username, which doesn't exist on this model — email is the closest equivalent identifier
    list_display = ("email", "full_name", "is_active", "is_staff", "subscription_status", "date_joined")
    list_filter = ("is_active", "is_staff", "subscription_status")
    search_fields = ("email", "full_name")

    # Controls the field groupings/layout on the "change user" detail page.
    # Rewritten from BaseUserAdmin's default (which references
    # "username"/"first_name"/"last_name") to match this model's actual
    # fields.
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name",)}),
        ("Subscription", {"fields": ("subscription_status",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    # Controls the (simpler) "add user" page — deliberately only asks for
    # email + password confirmation (password1/password2, provided by
    # UserCreationForm), not the full fieldsets above; an admin can fill in
    # the rest after the account exists.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    # Prevents admins from hand-editing these in the UI — date_joined is
    # auto_now_add (set once at creation) and last_login is maintained by
    # Django's auth system itself, so editing them here would be
    # meaningless/misleading.
    readonly_fields = ("date_joined", "last_login")
