__all__ = ()
from datetime import timedelta
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from project.models import Project, Rating, Tag
from user.models import User


class StaticUrlTest(TestCase):
    def test_home_endpoint(self):
        response = self.client.get(reverse('home:home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, reverse('authentication:login'))
        self.assertContains(response, reverse('authentication:registration'))
        self.assertNotContains(response, reverse('user:profile'))
        self.assertNotContains(response, reverse('user:projects'))
        self.assertNotContains(response, reverse('project:project_create'))
        self.assertContains(response, 'В каталоге пока нет проектов.')

    def test_signed_in_navigation(self):
        self.client.force_login(
            User.objects.create_user('reader', 'reader@example.test'),
        )
        response = self.client.get(reverse('home:home'))
        self.assertContains(response, reverse('user:profile'))
        self.assertContains(response, reverse('user:projects'))
        self.assertContains(response, reverse('project:project_create'))
        self.assertNotContains(
            response,
            reverse('authentication:registration'),
        )

    def test_home_shows_three_most_recently_updated_projects(self):
        owner = User.objects.create_user('author', 'author@example.test')
        now = timezone.now()
        projects = [
            Project.objects.create(
                name=f'Проект {number}',
                user=owner,
                document='projects/sample.pdf',
            )
            for number in range(4)
        ]
        for project, age in zip(projects, (0, 3, 2, 1)):
            Project.objects.filter(pk=project.pk).update(
                updated_at=now - timedelta(days=age),
            )
        newest = projects[0]
        tag = Tag.objects.create(name='Робототехника')
        newest.tags.add(tag)
        Rating.objects.create(project=newest, user=owner, value=9)

        response = self.client.get(reverse('home:home'))

        self.assertQuerySetEqual(
            response.context['recent_projects'],
            [newest, projects[3], projects[2]],
        )
        self.assertContains(response, newest.name)
        self.assertNotContains(response, projects[1].name)
        self.assertContains(
            response,
            reverse('project:project_detail', args=[newest.pk]),
        )
        self.assertContains(
            response,
            f'{reverse("project:project_list")}?tag={tag.slug}',
        )
        self.assertContains(response, '9,0')
