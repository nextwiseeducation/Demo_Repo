# Django admin's built-in forms for creating/editing users — subclassed
# here (rather than used directly) because they're hardcoded to Django's
# default User model's field set (username, etc.), which this project's
# custom User (models.py) doesn't have. These are used by UserAdmin in
# admin.py to make the admin's "add user" / "change user" pages work
# against our email-based model instead.
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        # Overrides the base form's model + fields: only email is collected
        # up front (the base form's Meta normally references
        # ["username"] via the default User model) — password1/password2
        # (confirmation) are handled by the base form itself and don't need
        # to be listed here.
        model = User
        fields = ("email",)


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
        # "__all__" is fine here (unlike the creation form) since this is
        # the admin's edit page, which is expected to expose every field —
        # UserAdmin.fieldsets in admin.py further controls layout/grouping,
        # this Meta just controls which fields the form is aware of at all.
        fields = "__all__"
