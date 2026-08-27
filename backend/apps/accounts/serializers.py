from django.contrib.auth import get_user_model
# Django's built-in password strength checker — runs every validator listed
# in AUTH_PASSWORD_VALIDATORS (settings/base.py: length, common-password,
# similarity-to-user-attributes, all-numeric checks). Passed as a DRF field
# validator below so weak passwords are rejected with the same rules on
# both registration and password reset.
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

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
    # write_only=True: this field is accepted on input (registration POST
    # body) but never included in the serialized output — critical, since
    # ModelSerializer would otherwise happily echo the raw password back in
    # the response. validators=[validate_password] runs Django's password
    # rules at serializer.is_valid() time, before create() is ever called.
    password = serializers.CharField(write_only=True, validators=[validate_password])
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
        return User.objects.create_user(
            **validated_data,
            disclaimer_accepted_at=timezone.now(),
            disclaimer_version=CURRENT_DISCLAIMER_VERSION,
            terms_accepted_at=timezone.now(),
            terms_version=CURRENT_TERMS_VERSION,
        )


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "full_name", "subscription_status"]
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
    # Same Django password-strength validator as RegisterSerializer, so a
    # password reset can't be used to set a weaker password than
    # registration would have allowed.
    new_password = serializers.CharField(validators=[validate_password])
