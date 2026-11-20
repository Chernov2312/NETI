__all__ = ()

from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from feedback.models import Feedback
from user.models import User


class FeedbackFormTests(TestCase):
    data = {
        'name': 'Анна',
        'email': 'anna@example.test',
        'message': 'Добавьте фильтр по автору проекта.',
    }

    def test_guest_can_submit_and_refresh_without_duplicate(self):
        url = reverse('feedback:form')
        home = self.client.get(reverse('home:home'))
        self.assertContains(home, url)
        response = self.client.post(
            url,
            {**self.data, 'status': Feedback.Status.CLOSED, 'note': 'лишнее'},
        )
        self.assertRedirects(response, url, fetch_redirect_response=False)
        self.assertContains(self.client.get(url), 'Ваше обращение отправлено.')
        self.client.get(url)
        entry = Feedback.objects.get()
        self.assertEqual(entry.email, self.data['email'])
        self.assertEqual(entry.message, self.data['message'])
        self.assertEqual(entry.status, Feedback.Status.NEW)
        self.assertEqual(entry.note, '')

    def test_feedback_validates_email_size_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse('feedback:form')
        self.assertEqual(client.post(url, self.data).status_code, 403)
        client.get(url)
        response = client.post(
            url,
            {
                **self.data,
                'email': 'invalid',
                'message': 'а' * 2001,
                'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
            },
        )
        form = response.context['form']
        self.assertTrue(form.has_error('email', 'invalid'))
        self.assertTrue(form.has_error('message', 'max_length'))
        self.assertFalse(Feedback.objects.exists())

    def test_form_prefills_an_authenticated_users_contact(self):
        user = User.objects.create_user(
            'anna', 'anna@example.test', first_name='Анна',
        )
        self.client.force_login(user)
        response = self.client.get(reverse('feedback:form'))
        form = response.context['form']
        self.assertEqual(form['name'].value(), 'Анна')
        self.assertEqual(form['email'].value(), user.email)


class FeedbackAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            'staff', 'staff@example.test', is_staff=True,
        )
        cls.entry = Feedback.objects.create(
            name='Анна',
            email='anna+feedback@example.test',
            message='Текст обращения',
        )

    def test_feedback_admin_requires_permission(self):
        url = reverse('admin:feedback_feedback_changelist')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_can_search_and_process_feedback(self):
        self.staff.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label='feedback',
                codename__in=['view_feedback', 'change_feedback'],
            ),
        )
        self.client.force_login(self.staff)
        listing = reverse('admin:feedback_feedback_changelist')
        response = self.client.get(listing, {'q': 'anna'})
        self.assertContains(response, self.entry.email)
        response = self.client.get(listing, {'status__exact': 'closed'})
        self.assertNotContains(response, self.entry.email)

        url = reverse('admin:feedback_feedback_change', args=[self.entry.pk])
        response = self.client.get(url)
        self.assertContains(response, 'mailto:anna%2Bfeedback@example.test')
        response = self.client.post(
            url,
            {
                'status': Feedback.Status.CLOSED,
                'note': 'Проверили вопрос.',
                'message': 'Попытка изменить исходный текст',
                '_save': '1',
            },
        )
        self.assertRedirects(response, listing)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.status, Feedback.Status.CLOSED)
        self.assertEqual(self.entry.note, 'Проверили вопрос.')
        self.assertEqual(self.entry.message, 'Текст обращения')
