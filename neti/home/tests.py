__all__ = ()
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from user.models import User


class StaticUrlTest(TestCase):
    def test_home_endpoint(self):
        response = self.client.get(reverse('home:home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, reverse('authentication:login'))
        self.assertContains(response, reverse('authentication:registration'))
        self.assertNotContains(response, reverse('user:profile'))
        self.assertNotContains(response, reverse('user:projects'))

    def test_signed_in_navigation(self):
        self.client.force_login(
            User.objects.create_user('reader', 'reader@example.test'),
        )
        response = self.client.get(reverse('home:home'))
        self.assertContains(response, reverse('user:profile'))
        self.assertContains(response, reverse('user:projects'))
        self.assertNotContains(
            response,
            reverse('authentication:registration'),
        )
