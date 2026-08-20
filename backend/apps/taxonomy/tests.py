from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import ClientNeedsCategory, ExamType


class ClientNeedsCategoryTests(TestCase):
    def test_rn_and_pn_can_share_a_name(self):
        rn = ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.RN)
        pn = ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.PN)
        self.assertNotEqual(rn.pk, pn.pk)
        self.assertEqual(str(rn), "Management of Care (RN)")

    def test_duplicate_name_and_exam_type_rejected(self):
        ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.RN)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.RN)

    def test_defaults_to_rn(self):
        category = ClientNeedsCategory.objects.create(name="Safety and Infection Control")
        self.assertEqual(category.exam_type, ExamType.RN)
