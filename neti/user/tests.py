__all__ = ()

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from project.models import Project
from user.models import User


class UserPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'reader', 'reader@example.test', role='moderator',
        )
        another = User.objects.create_user('author', 'author@example.test')
        Project.objects.create(
            name='Мой проект',
            user=cls.user,
            document='a.pdf',
        )
        Project.objects.create(
            name='Чужой проект',
            user=another,
            document='b.pdf',
        )

    def test_personal_pages_require_login(self):
        login_url = reverse('authentication:login')
        for name in ('user:profile', 'user:projects'):
            with self.subTest(name=name):
                url = reverse(name)
                self.assertRedirects(
                    self.client.get(url),
                    f'{login_url}?next={url}',
                )

    def test_profile_uses_user_fields(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('user:profile'))
        self.assertTemplateUsed(response, 'user/profile.html')
        self.assertContains(response, self.user.email)
        self.assertContains(response, 'Модератор')
        self.assertContains(response, reverse('user:projects'))
        self.assertContains(response, reverse('authentication:logout'))

    def test_my_projects_lists_only_own_projects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('user:projects'))
        self.assertContains(response, 'Мой проект')
        self.assertNotContains(response, 'Чужой проект')


class UserAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user('student', 'student@test.test')
        cls.superuser = User.objects.create_superuser(
            'admin', 'admin@test.test',
        )
        cls.staff = User.objects.create_user(
            'staff', 'staff@test.test', is_staff=True,
        )
        cls.staff.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='user',
                codename='change_user',
            ),
        )

    def test_superuser_can_assign_and_revoke_moderator_role(self):
        self.client.force_login(self.superuser)
        url = reverse('admin:user_user_change', args=[self.student.pk])
        self.assertContains(self.client.get(url), 'Роль в каталоге')
        joined = timezone.localtime(self.student.date_joined)
        for role in (User.Role.MODERATOR, User.Role.STUDENT):
            with self.subTest(role=role):
                response = self.client.post(
                    url,
                    {
                        'username': self.student.username,
                        'email': self.student.email,
                        'is_active': True,
                        'role': role,
                        'date_joined_0': joined.date().isoformat(),
                        'date_joined_1': joined.strftime('%H:%M:%S'),
                        '_save': '1',
                    },
                )
                self.assertRedirects(
                    response,
                    reverse('admin:user_user_changelist'),
                )
                self.student.refresh_from_db()
                self.assertEqual(self.student.role, role)

    def test_staff_cannot_assign_moderator_role(self):
        self.client.force_login(self.staff)
        url = reverse('admin:user_user_change', args=[self.student.pk])
        response = self.client.post(url, {'role': User.Role.MODERATOR})
        self.assertEqual(response.status_code, 403)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.Role.STUDENT)
