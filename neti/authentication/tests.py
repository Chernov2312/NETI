__all__ = ()

from unittest.mock import patch
from urllib.parse import urlsplit

from django.contrib.auth import SESSION_KEY
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from authentication.forms import UserRegisterForm
from user.models import User


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class AuthenticationTests(TestCase):
    password = 'A-long-test-passphrase#78'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'student', 'student@example.test', cls.password,
        )

    def test_registration(self):
        url = reverse('authentication:registration')
        data = {
            'username': 'new-student',
            'email': 'New-Student@Example.Test',
            'password1': self.password,
            'password2': self.password,
            'role': 'moderator',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('authentication:login'))
        user = User.objects.get(username=data['username'])
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(user.role, 'student')
        self.assertEqual(user.email, 'new-student@example.test')

        response = self.client.post(url, {**data, 'username': 'other-student'})
        self.assertFormError(
            response.context['form'],
            'email',
            'Этот адрес электронной почты уже используется.',
        )
        self.assertFalse(
            User.objects.filter(username='other-student').exists(),
        )

    def test_registration_displays_localized_errors_without_passwords(self):
        response = self.client.post(
            reverse('authentication:registration'),
            {
                'username': 'STUDENT',
                'email': self.user.email.upper(),
                'password1': self.password,
                'password2': 'Different-passphrase#31',
            },
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'username',
            'Это имя пользователя уже занято.',
        )
        self.assertFormError(
            form,
            'email',
            'Этот адрес электронной почты уже используется.',
        )
        self.assertIn('password2', form.errors)
        self.assertContains(response, 'Исправьте отмеченные поля')
        self.assertContains(response, 'aria-invalid="true"', count=3)
        self.assertNotContains(response, self.password)
        self.assertNotContains(response, 'Different-passphrase#31')
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_overlong_username(self):
        response = self.client.post(
            reverse('authentication:registration'),
            {
                'username': 'a' * 151,
                'email': 'another@example.test',
                'password1': self.password,
                'password2': self.password,
            },
        )
        errors = response.context['form'].errors.as_data()
        self.assertEqual(errors['username'][0].code, 'max_length')
        self.assertEqual(User.objects.count(), 1)

    def test_registration_handles_email_taken_before_save(self):
        original_validation = UserRegisterForm.is_valid
        email = 'race@example.test'

        def validate_before_other_registration(form):
            valid = original_validation(form)
            if valid:
                User.objects.create_user('other-registration', email)
            return valid

        with patch.object(
            UserRegisterForm,
            'is_valid',
            validate_before_other_registration,
        ):
            response = self.client.post(
                reverse('authentication:registration'),
                {
                    'username': 'late-registration',
                    'email': email.upper(),
                    'password1': self.password,
                    'password2': self.password,
                },
            )

        self.assertFormError(
            response.context['form'],
            'email',
            'Этот адрес электронной почты уже используется.',
        )
        self.assertEqual(
            User.objects.get(email=email).username, 'other-registration',
        )
        self.assertFalse(
            User.objects.filter(username='late-registration').exists(),
        )

    def test_login_by_username_or_email(self):
        for identifier in (
            self.user.username,
            self.user.email,
            self.user.email.upper(),
        ):
            with self.subTest(identifier=identifier):
                self.client.logout()
                response = self.client.post(
                    reverse('authentication:login'),
                    {'login': identifier, 'password': self.password},
                )
                self.assertRedirects(response, reverse('project:project_list'))
                self.assertEqual(
                    self.client.session[SESSION_KEY],
                    str(self.user.pk),
                )

    def test_login_uses_exact_email_for_legacy_case_duplicates(self):
        legacy = User.objects.create_user(
            'legacy', 'Student@example.test', self.password,
        )
        url = reverse('authentication:login')
        response = self.client.post(
            url, {'login': 'STUDENT@example.test', 'password': self.password},
        )
        self.assertContains(response, 'Неверный логин или пароль.')
        self.assertNotIn(SESSION_KEY, self.client.session)

        response = self.client.post(
            url, {'login': legacy.email, 'password': self.password},
        )
        self.assertRedirects(response, reverse('project:project_list'))
        self.assertEqual(self.client.session[SESSION_KEY], str(legacy.pk))

    def test_login_rejects_wrong_credentials_and_inactive_user(self):
        url = reverse('authentication:login')
        for password, is_active in (('wrong', True), (self.password, False)):
            with self.subTest(password=password):
                User.objects.filter(pk=self.user.pk).update(
                    is_active=is_active,
                )
                response = self.client.post(
                    url,
                    {'login': self.user.email, 'password': password},
                )
                self.assertContains(response, 'Неверный логин или пароль.')
                self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_redirects_only_to_valid_next(self):
        profile_url = reverse('user:profile')
        for next_url, target in (
            (profile_url, profile_url),
            ('https://example.test', reverse('project:project_list')),
        ):
            with self.subTest(next_url=next_url):
                response = self.client.post(
                    reverse('authentication:login'),
                    {
                        'login': self.user.username,
                        'password': self.password,
                        'next': next_url,
                    },
                )
                self.assertRedirects(response, target)

    def test_logout_requires_post_with_csrf_and_ends_session(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        url = reverse('authentication:logout')
        self.assertEqual(client.get(url).status_code, 405)
        self.assertEqual(client.post(url).status_code, 403)
        self.assertIn(SESSION_KEY, client.session)

        client.get(reverse('user:profile'))
        token = client.cookies['csrftoken'].value
        response = client.post(url, {'csrfmiddlewaretoken': token})
        self.assertRedirects(response, reverse('home:home'))
        self.assertNotIn(SESSION_KEY, client.session)

    def test_password_reset_email_link_can_be_used_once(self):
        url = reverse('authentication:password_reset')
        self.assertContains(
            self.client.get(reverse('authentication:login')),
            url,
        )
        response = self.client.post(
            url, {'email': self.user.email}, secure=True,
        )
        self.assertRedirects(
            response,
            reverse('authentication:password_reset_done'),
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertEqual(email.subject, 'Сброс пароля NETI')
        link = next(line for line in email.body.splitlines() if '://' in line)
        self.assertEqual(urlsplit(link).scheme, 'https')

        token_url = urlsplit(link).path
        response = self.client.get(token_url, follow=True, secure=True)
        self.assertTrue(response.context['validlink'])
        confirm_url = response.redirect_chain[-1][0]
        new_password = 'New-passphrase-for-NETI#52'
        response = self.client.post(
            confirm_url,
            {'new_password1': new_password, 'new_password2': new_password},
            secure=True,
        )
        self.assertRedirects(
            response,
            reverse('authentication:password_reset_complete'),
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password(self.password))
        response = self.client.get(token_url, secure=True)
        self.assertFalse(response.context['validlink'])
        self.assertContains(response, 'Запросить новую ссылку')

    def test_password_reset_response_is_generic(self):
        inactive = User.objects.create_user(
            'inactive',
            'inactive@example.test',
            self.password,
            is_active=False,
        )
        unusable = User.objects.create_user('no-password', 'none@example.test')
        url = reverse('authentication:password_reset')
        sent_url = reverse('authentication:password_reset_done')

        for email in (inactive.email, unusable.email, 'unknown@example.test'):
            with self.subTest(email=email):
                response = self.client.post(url, {'email': email})
                self.assertRedirects(response, sent_url)
                self.assertEqual(len(mail.outbox), 0)

        response = self.client.get(sent_url)
        self.assertContains(response, 'Если на этот адрес')
