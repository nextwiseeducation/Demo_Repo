from django.conf import settings
from django.core.mail import send_mail

from .tokens import make_verification_token


def send_verification_email(user):
    token = make_verification_token(user.pk)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_mail(
        subject="Verify your NextWise Education account",
        message=f"Welcome to NextWise Education. Verify your email to activate your account:\n\n{verify_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user, uid, token):
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="Reset your NextWise Education password",
        message=f"Reset your password using the link below:\n\n{reset_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
