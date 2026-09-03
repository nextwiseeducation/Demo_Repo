from django.contrib.auth import get_user_model

# Django's built-in password strength checker — runs every validator listed
# in AUTH_PASSWORD_VALIDATORS (settings/base.py: length, common-password,
# similarity-to-user-attributes, all-numeric checks).
#
# It is deliberately NOT attached as a DRF field validator
# (validators=[validate_password]) any more. A field validator is called
# with the value alone, so validate_password() received user=None and
# UserAttributeSimilarityValidator — the one configured specifically to
# reject a password that is a lightly-disguised copy of the student's own
# email or name — silently did nothing at all. It is now called from
# validate() (registration) and from the view (password reset confirm),
# in both cases with an actual User object, so that validator can do its
# job.
from django.contrib.auth.password_validation import validate_password

# Django's ValidationError (not DRF's) is what validate_password raises;
# it has to be caught and re-raised as a DRF ValidationError so the failure
# comes back as a normal 400 with per-field errors rather than a 500.
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# get_user_model() (rather than importing User directly from .models) is
# the Django-recommended way to reference the active user model — respects
# AUTH_USER_MODEL and avoids a hard import-time dependency on this specific
# app's models module.
User = get_user_model()

# Current NCLEX Examination Disclaimer text version — bump this (and update
# the frontend copy + TermsAndConditionsPage anchor) whenever the disclaimer
# wording materially changes, so disclaimer_accepted records stay tied to
# the exact text a student agreed to.
CURRENT_DISCLAIMER_VERSION = "1.0"
# Same idea, for the Privacy Policy + Terms and Conditions checkbox — bump
# independently of CURRENT_DISCLAIMER_VERSION, since these are separate
# legal documents that change on their own schedule.
CURRENT_TERMS_VERSION = "1.0"


class RegisterSerializer(serializers.ModelSerializer):
    # Declared explicitly rather than being auto-generated from the model
    # field, purely to DROP the UniqueValidator that ModelSerializer would
    # otherwise attach because User.email is unique=True. That validator
    # turned a duplicate registration into a 400 "user with this email
    # already exists", which is a user-enumeration oracle: anyone could
    # probe the register endpoint to learn which email addresses have
    # accounts here. The password-reset endpoint goes to real trouble to
    # avoid exactly that leak, so registration must not undo it.
    #
    # RegisterView now does the duplicate check itself and returns the same
    # generic 201 either way (emailing the real owner instead of creating a
    # second account). unique=True stays on the MODEL: the database
    # constraint is the actual integrity guarantee, and it still makes two
    # simultaneous registrations of the same address fail safely.
    email = serializers.EmailField()
    # write_only=True: this field is accepted on input (registration POST
    # body) but never included in the serialized output — critical, since
    # ModelSerializer would otherwise happily echo the raw password back in
    # the response. Strength checking happens in validate() below rather
    # than here — see the validate_password import comment for why.
    password = serializers.CharField(write_only=True)
    # write_only + not a model field (popped in create() below) — this is
    # the server-side gate behind the registration-page checkbox. It exists
    # so liability protection doesn't rest solely on client-side JS: a
    # direct POST to this endpoint that omits/falsifies the field is
    # rejected here, same as any other required field.
    accepted_disclaimer = serializers.BooleanField(write_only=True)
    # Same server-side-gate reasoning as accepted_disclaimer above, for the
    # separate Privacy Policy + Terms and Conditions checkbox — a distinct
    # legal acknowledgment, so it's validated and recorded independently
    # rather than reusing the disclaimer's field/flag.
    accepted_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        # Only these fields are accepted from the registration request
        # body — is_active/is_staff/subscription_status etc. are
        # deliberately NOT listed, so a malicious payload can't set
        # is_staff=true from the public registration endpoint.
        fields = ["email", "password", "full_name", "accepted_disclaimer", "accepted_terms"]

    def validate_accepted_disclaimer(self, value):
        # BooleanField already coerces to True/False, so the only case to
        # reject here is an explicit False (or an omitted field, which
        # BooleanField treats as required and rejects before this runs) —
        # registration must not proceed without an affirmative acceptance.
        if value is not True:
            raise serializers.ValidationError(
                "You must acknowledge the NCLEX Examination Disclaimer to register."
            )
        return value

    def validate_accepted_terms(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "You must agree to the Privacy Policy and Terms and Conditions to register."
            )
        return value

    def validate(self, attrs):
        # Object-level (not field-level) validation, because this is the
        # only place a *whole* candidate user is available. The unsaved
        # User(...) below is never written to the database — it exists
        # solely to hand validate_password() the email and full_name the
        # student just submitted, which is what
        # UserAttributeSimilarityValidator compares the password against.
        # Without it, "student@example.com" / "studentexample" would sail
        # straight through.
        candidate = User(email=attrs.get("email", ""), full_name=attrs.get("full_name", ""))
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            # Re-raised keyed on "password" (rather than as a non-field
            # error) so the response body keeps the same shape the frontend
            # registration form already reads — it maps field errors back
            # onto the matching input.
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        # Not User model fields — must be popped before create_user(**...)
        # is called, or Django would raise a TypeError for unexpected
        # keyword arguments.
        validated_data.pop("accepted_disclaimer")
        validated_data.pop("accepted_terms")
        # Routes through User.objects.create_user (see models.py's
        # UserManager) rather than User.objects.create(**validated_data) —
        # essential, because create_user is what hashes the password via
        # set_password(); a plain create() would store the raw password
        # text as-is.
        # One timestamp captured once, not two separate timezone.now()
        # calls. Ticking the clock between the two would record the
        # disclaimer and the terms as accepted microseconds apart, which is
        # false: the student submitted one form, in one act of acceptance.
        # These fields are a legal audit trail, so they should say exactly
        # that.
        now = timezone.now()
        return User.objects.create_user(
            **validated_data,
            disclaimer_accepted_at=now,
            disclaimer_version=CURRENT_DISCLAIMER_VERSION,
            terms_accepted_at=now,
            terms_version=CURRENT_TERMS_VERSION,
        )


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # role is included so the frontend can gate the admin dashboard nav
        # and routes (RequireRole) off the same object AuthContext already
        # fetches on login/bootstrap — no JWT decoding, no extra request,
        # and it stays fresh on every /me/ call rather than living in a
        # token claim for up to the refresh token's 14-day lifetime.
        fields = ["email", "full_name", "subscription_status", "role"]
        # read_only_fields = fields marks every listed field read-only in
        # one line — appropriate here since MeSerializer is only ever used
        # to serialize the current user for GET /api/auth/me/ (see
        # MeView in views.py), never to accept input/updates.
        read_only_fields = fields


class PasswordResetRequestSerializer(serializers.Serializer):
    # Plain Serializer (not ModelSerializer) since this isn't
    # creating/updating a User row directly — it's just validating the
    # shape of "give me an email address" input for
    # PasswordResetRequestView.
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    # uid/token together identify which user + prove the reset link is
    # legitimate (see PasswordResetConfirmView in views.py for how they're
    # decoded/checked) — both are opaque strings from the reset-link the
    # user clicked, not looked up or validated by the serializer itself.
    uid = serializers.CharField()
    token = serializers.CharField()
    # The same Django password-strength rules as RegisterSerializer apply
    # here, so a reset can't be used to set a weaker password than
    # registration would have allowed — but they are NOT attached as a
    # field validator. Checking strength needs the User object (see the
    # validate_password import comment), and which user this is only
    # becomes known after uid/token have been decoded and verified, which
    # is PasswordResetConfirmView's job. So the view calls
    # validate_password(new_password, user) itself once it has resolved the
    # user, and returns a 400 keyed on "new_password" — the identical error
    # shape a field validator would have produced, which is what the reset
    # form on the frontend reads.
    new_password = serializers.CharField()


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Adds the user's role as a JWT claim, so a consumer holding only the
    token (not a live session) can read it without a database round trip.

    IMPORTANT: this claim is NOT the source of truth authorization is
    decided from — apps.accounts.permissions.IsSuperuser/
    IsContentAdminOrAbove read request.user.role straight from the
    database on every request. See those classes' docstrings for why: a
    role demoted server-side must not remain valid via a stale token claim
    for up to the refresh token's lifetime.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token
