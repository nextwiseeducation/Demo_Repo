# AbstractBaseUser gives us password hashing/checking (set_password,
# check_password) and last_login tracking without any of the default
# User model's username-based fields — we build our own field set on top.
# BaseUserManager is the base class for the custom manager below (needed
# because create_user()/create_superuser() aren't provided automatically
# when using AbstractBaseUser, unlike Django's default User).
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
# PermissionsMixin adds is_superuser, groups, user_permissions, and the
# has_perm()/has_module_perms() methods — needed so this custom User can
# still be used with Django's permission system and the admin site.
from django.contrib.auth.models import PermissionsMixin
from django.db import models

# Shared abstract mixins (see apps/core/models.py) — UUIDPKMixin gives this
# model a UUID primary key instead of an auto-increment int; TimeStampedMixin
# is deliberately NOT used here even though other models use it, because
# AbstractBaseUser already provides its own timing field (date_joined is
# redefined below rather than inherited, and there's no updated_at need for
# User specifically).
from apps.core.models import TimeStampedMixin, UUIDPKMixin


class UserManager(BaseUserManager):
    """
    Custom manager required because AbstractBaseUser (unlike Django's
    default User) does not ship with create_user/create_superuser — we have
    to define how a User is actually constructed, including "what counts as
    the username" (email, not a separate username field) and password
    hashing (via set_password, which salts+hashes rather than storing plain
    text).
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        # normalize_email lowercases the domain part only (per RFC, the
        # local part before @ can be case-sensitive) — keeps
        # "a@Example.com" and "a@example.com" from being treated as
        # different accounts purely due to domain casing.
        email = self.normalize_email(email)
        # self.model refers to whatever model this manager is attached to
        # (User) — using self.model instead of importing User directly
        # avoids a circular import and lets this manager be reused if the
        # model were ever swapped/subclassed.
        user = self.model(email=email, **extra_fields)
        # set_password hashes the raw password (Django's configured hasher,
        # PBKDF2 by default) before it ever touches the database — the raw
        # value is never stored or logged.
        user.set_password(password)
        # using=self._db routes the write to whichever database this
        # manager is bound to, respecting Django's multi-database routing
        # if it's ever introduced (currently there's only one DB, but this
        # is the standard/safe pattern regardless).
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # setdefault (not a plain assignment) so an explicit False passed by
        # a caller isn't silently overwritten — though the checks below
        # then immediately reject that case anyway, since a superuser must
        # have both flags True.
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)  # superusers created via `createsuperuser` should be able to log in immediately, bypassing the normal email-verification gate

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        # Delegates to create_user for the actual construction/hashing/save,
        # so there's exactly one code path that creates a User row.
        return self.create_user(email, password, **extra_fields)


class SubscriptionStatus(models.TextChoices):
    """
    TextChoices generates both the stored string value (e.g. "FREE") and a
    human-readable label ("Free") for admin/forms — used as the `choices=`
    for User.subscription_status below. Kept intentionally small/generic
    here (vs. the more Stripe-shaped SubscriptionStatus in apps.payments,
    which includes TRIALING/UNPAID/INCOMPLETE) since this field is just a
    denormalized display cache, not the payments system of record.
    """

    FREE = "FREE", "Free"
    ACTIVE = "ACTIVE", "Active"
    PAST_DUE = "PAST_DUE", "Past due"
    CANCELED = "CANCELED", "Canceled"


class User(UUIDPKMixin, AbstractBaseUser, PermissionsMixin):
    """
    Custom user model, email as the login identifier — no separate username.

    subscription_status is a denormalized cache of the student's current
    UserSubscription.status (apps.payments), kept here so permission checks
    on question/quiz endpoints don't need a join on every request. It has no
    write path yet in Milestone 1 — the sync from Stripe webhooks lands in
    Phase 2, so every account defaults to FREE until then.
    """

    # unique=True is what makes email usable as the login identifier
    # (USERNAME_FIELD below) — the database enforces no two users can share
    # an email, which registration also relies on implicitly (a second
    # create_user with the same email raises an IntegrityError).
    email = models.EmailField(unique=True)
    # blank=True (form-level: optional) but no null=True — CharFields store
    # "no value" as an empty string, not NULL, per Django convention; keeps
    # `if not user.full_name` checks simple without also handling None.
    full_name = models.CharField(max_length=255, blank=True)
    # Defaults to False: a newly registered account cannot log in until
    # email verification flips this to True (see VerifyEmailView in
    # views.py). This is what actually enforces "you must verify your email
    # before using the account" — Django's auth backend checks is_active
    # during authenticate().
    is_active = models.BooleanField(default=False)
    # Whether this user can access the Django admin site at all (separate
    # from is_superuser, which grants blanket permissions once inside).
    is_staff = models.BooleanField(default=False)
    # auto_now_add=True: set once at creation, never changes afterward —
    # same behavior as TimeStampedMixin.created_at, but defined directly
    # here (rather than inheriting that mixin) since User only needs this
    # one timestamp field, not also an updated_at.
    date_joined = models.DateTimeField(auto_now_add=True)
    subscription_status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.FREE
    )

    # Attaches the custom manager so User.objects.create_user(...) /
    # .create_superuser(...) work — without this, Django would use the
    # default manager, which doesn't know about email-based creation.
    objects = UserManager()

    # Tells Django's auth system "email is the field used to log in" —
    # this is what makes `authenticate(email=..., password=...)` and the
    # JWT login serializer work, instead of expecting a `username` field.
    USERNAME_FIELD = "email"
    # Fields prompted for by `createsuperuser` beyond USERNAME_FIELD and
    # password — empty because email + password is sufficient; full_name is
    # optional and not required at account-creation time.
    REQUIRED_FIELDS = []

    def __str__(self):
        # Used anywhere Django renders a User as text — admin list/detail
        # pages, shell debugging, etc. Email is the natural human-readable
        # identifier here since there's no username.
        return self.email
