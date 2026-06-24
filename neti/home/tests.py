__all__ = ()
from http import HTTPStatus

from django.test import TestCase


class StaticUrlTest(TestCase):
    def test_home_endpoint(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, HTTPStatus.OK)
