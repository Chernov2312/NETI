__all__ = ()

from django.conf import settings
from django.test.runner import DiscoverRunner


class ProjectDiscoverRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, **kwargs):
        return super().build_suite(
            test_labels or [str(settings.BASE_DIR)],
            **kwargs,
        )
