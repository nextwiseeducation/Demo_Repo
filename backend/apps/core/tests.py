from django.test import TestCase

# No tests here directly — UUIDPKMixin/TimeStampedMixin are exercised
# indirectly by every other app's model tests (e.g. any test that creates a
# Question and checks its id is a UUID, or that created_at gets set, is
# implicitly testing this app's mixins).
# Create your tests here.
