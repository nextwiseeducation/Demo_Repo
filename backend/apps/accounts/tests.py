from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from .tokens import make_verification_token

User = get_user_model()


class RegistrationAndVerificationTests(APITestCase):
    def test_register_creates_inactive_user_and_sends_email(self):
        response = self.client.post(
            reverse("register"),
            {"email": "student@example.com", "password": "a-strong-password-123", "full_name": "Jane Student"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="student@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].subject.lower())

    def test_verify_email_activates_account(self):
        user = User.objects.create_user(email="student@example.com", password="a-strong-password-123")
        self.assertFalse(user.is_active)

        token = make_verification_token(user.pk)
        response = self.client.get(reverse("verify-email", args=[token]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_verify_email_rejects_invalid_token(self):
        response = self.client.get(reverse("verify-email", args=["not-a-real-token"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.password = "a-strong-password-123"
        self.active_user = User.objects.create_user(
            email="active@example.com", password=self.password, is_active=True
        )
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com", password=self.password, is_active=False
        )

    def test_login_succeeds_for_verified_user(self):
        response = self.client.post(reverse("login"), {"email": "active@example.com", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejected_for_unverified_user(self):
        response = self.client.post(reverse("login"), {"email": "inactive@example.com", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(email="student@example.com", password="a-strong-password-123", is_active=True)
        login_response = self.client.post(
            reverse("login"), {"email": "student@example.com", "password": "a-strong-password-123"}
        )
        access, refresh = login_response.data["access"], login_response.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = self.client.post(reverse("logout"), {"refresh": refresh})
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_response = self.client.post(reverse("token-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="student@example.com", password="old-password-123", is_active=True)

    def test_request_reset_sends_email_for_existing_user(self):
        response = self.client.post(reverse("password-reset"), {"email": "student@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_request_reset_does_not_leak_unknown_email(self):
        response = self.client.post(reverse("password-reset"), {"email": "nobody@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_reset_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "a-new-strong-password-456"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("a-new-strong-password-456"))

    def test_confirm_reset_rejects_bad_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": "bad-token", "new_password": "a-new-strong-password-456"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
