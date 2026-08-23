# IntegrityError is what the database driver raises when a constraint
# (here, unique_together) is violated; transaction.atomic() is required to
# wrap the call that's expected to fail, because Django's test runner
# already wraps each test in an outer transaction, and a raised
# IntegrityError otherwise poisons that whole outer transaction for the
# rest of the test — the atomic() block gives the failure its own
# sub-transaction to roll back instead.
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import ClientNeedsCategory, ExamType


class ClientNeedsCategoryTests(TestCase):
    """
    Specifically tests the exam_type field's reason for existing (see the
    docstring on ClientNeedsCategory in models.py) — that RN and PN can
    each have their own category with the same name, but the same exam
    type can't have true duplicates.
    """

    def test_rn_and_pn_can_share_a_name(self):
        rn = ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.RN)
        pn = ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.PN)
        # Confirms these are genuinely two separate rows, not e.g. a
        # get_or_create-style silent no-op that returned the same row twice.
        self.assertNotEqual(rn.pk, pn.pk)
        self.assertEqual(str(rn), "Management of Care (RN)")

    def test_duplicate_name_and_exam_type_rejected(self):
        ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.RN)
        # The second create with the identical (name, exam_type) pair must
        # violate the unique_together constraint from models.py's Meta.
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClientNeedsCategory.objects.create(name="Management of Care", exam_type=ExamType.RN)

    def test_defaults_to_rn(self):
        # exam_type isn't passed at all here — confirms the field's
        # default=ExamType.RN actually takes effect, which matters since
        # Phase 1 only seeds RN categories and relies on this default for
        # any category created without the field being set explicitly.
        category = ClientNeedsCategory.objects.create(name="Safety and Infection Control")
        self.assertEqual(category.exam_type, ExamType.RN)
