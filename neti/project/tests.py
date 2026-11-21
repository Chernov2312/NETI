__all__ = ()

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image as PillowImage

from project.forms import MAX_DOCUMENT_SIZE, MAX_IMAGE_SIZE
from project.models import (
    Image,
    MainImage,
    Opportunity,
    Project,
    ProjectReport,
    Rating,
    Tag,
)
from project.views import PROJECTS_PER_PAGE
from user.models import User


class ProjectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('owner', 'owner@example.test')
        cls.reader = User.objects.create_user('reader', 'reader@example.test')
        cls.moderator = User.objects.create_user(
            'moderator', 'moderator@example.test', role='moderator',
        )
        cls.project = Project.objects.create(
            name='Робот',
            description='Описание робота',
            document='old-document.docx',
            user=cls.owner,
        )
        cls.tag = Tag.objects.create(name='Робототехника')
        cls.project.tags.add(cls.tag)

    def setUp(self):
        media = self.enterContext(TemporaryDirectory())
        self.media = Path(media)
        self.enterContext(override_settings(MEDIA_ROOT=self.media))
        self.detail_url = self.project_url('project_detail')
        self.create_url = reverse('project:project_create')

    def project_url(self, action, project=None):
        project = project or self.project
        return reverse(f'project:{action}', args=[project.pk])

    @staticmethod
    def pdf():
        return SimpleUploadedFile('document.pdf', b'%PDF-1.7\n%%EOF\n')

    @staticmethod
    def png(name='robot.png', size=(16, 16), image_format='PNG'):
        buffer = BytesIO()
        PillowImage.new('1', size).save(buffer, format=image_format)
        return SimpleUploadedFile(name, buffer.getvalue())

    def create_project(self, **extra):
        self.client.force_login(self.owner)
        response = self.client.post(
            self.create_url,
            {'name': 'Новый проект', 'document': self.pdf(), **extra},
        )
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(name='Новый проект')
        self.assertRedirects(
            response,
            self.project_url('project_detail', project),
        )
        return project

    def test_detail_and_unknown_uuid(self):
        response = self.client.get(self.detail_url)
        self.assertTemplateUsed(response, 'project/item_info.html')
        self.assertContains(response, self.project.description)
        self.assertContains(response, self.tag.name)
        self.assertContains(response, 'Оценок пока нет.')
        self.assertNotContains(response, self.project_url('project_edit'))
        unknown = reverse('project:project_detail', args=[uuid4()])
        self.assertEqual(self.client.get(unknown).status_code, 404)

    def test_catalog_placeholder_and_tag_filter(self):
        Project.objects.create(
            name='Другой проект', user=self.owner, document='other.pdf',
        )
        url = reverse('project:project_list')
        response = self.client.get(url)
        self.assertContains(response, 'Нет изображения')
        self.assertContains(response, 'Другой проект')
        response = self.client.get(url, {'tag': self.tag.slug})
        self.assertContains(response, self.detail_url)
        self.assertContains(response, self.tag.name)
        self.assertNotContains(response, 'Другой проект')
        response = self.client.get(url, {'tag': 'missing'})
        self.assertEqual(response.status_code, 404)

    def test_opportunity_marketplace_submission_and_contact(self):
        url = reverse('project:opportunity_list')
        create_url = reverse('project:opportunity_create')
        response = self.client.get(url)
        self.assertContains(response, 'Биржа заданий')
        self.assertNotContains(response, create_url)

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(create_url).status_code, 403)
        self.assertEqual(
            self.client.post(
                create_url,
                {'title': 'Запретное задание', 'organization': 'Вуз'},
            ).status_code,
            403,
        )
        self.assertFalse(Opportunity.objects.exists())

        university = User.objects.create_user(
            'university', 'lab@example.test', role='university',
        )
        self.client.force_login(university)
        response = self.client.post(
            create_url,
            {
                'title': 'Система мониторинга воздуха',
                'kind': Opportunity.Kind.BRIEF,
                'organization': 'Институт экологии НГТУ',
                'description': 'Создать прототип датчика и описать испытания.',
                'contact_email': 'lab@example.test',
                'deadline': '2027-04-30',
            },
        )
        opportunity = Opportunity.objects.get()
        self.assertRedirects(
            response,
            reverse('project:opportunity_detail', args=[opportunity.pk]),
        )
        self.assertEqual(opportunity.author, university)
        self.assertContains(self.client.get(url), opportunity.title)
        detail_url = reverse(
            'project:opportunity_detail', args=[opportunity.pk],
        )
        detail = self.client.get(detail_url)
        self.assertContains(detail, opportunity.description)
        self.assertContains(detail, 'mailto:lab@example.test')
        self.assertContains(detail, 'Снять задание с биржи')

        self.client.force_login(self.reader)
        self.assertEqual(
            self.client.post(
                reverse('project:opportunity_delete', args=[opportunity.pk]),
            ).status_code,
            403,
        )
        self.client.force_login(university)
        self.assertRedirects(
            self.client.post(
                reverse('project:opportunity_delete', args=[opportunity.pk]),
            ),
            url,
        )
        self.assertFalse(Opportunity.objects.exists())

    def test_project_pages_handle_missing_image_files(self):
        cover = MainImage.objects.create(
            project=self.project,
            main_image='missing/cover.png',
        )
        photo = Image.objects.create(
            project=self.project,
            image='missing/photo.png',
        )

        with self.assertNoLogs('sorl.thumbnail', level='WARNING'):
            catalog = self.client.get(reverse('project:project_list'))
            home = self.client.get(reverse('home:home'))
            detail = self.client.get(self.detail_url)

        self.assertContains(catalog, 'Нет изображения')
        self.assertContains(home, 'project-cover-placeholder')
        self.assertNotContains(catalog, 'src="/media/cache/')
        self.assertNotContains(home, 'src="/media/cache/')
        self.assertNotContains(detail, cover.main_image.url)
        self.assertNotContains(detail, photo.image.url)
        self.assertNotContains(detail, 'Галерея')

        cover.main_image.storage.save(cover.main_image.name, self.png())
        for url_name in ('project:project_list', 'home:home'):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertContains(response, 'src="/media/cache/')

    def test_catalog_search_matches_part_of_title_with_selected_tag(self):
        station = Project.objects.create(
            name='Arduino: датчик 100%',
            user=self.owner,
            document='station.pdf',
        )
        Project.objects.create(
            name='Arduino: датчик 1000',
            user=self.owner,
            document='untagged.pdf',
        )
        description_only = Project.objects.create(
            name='Другая станция',
            description='Arduino: датчик 100%',
            user=self.owner,
            document='description.pdf',
        )
        self.tag.projects.add(station, description_only)
        url = reverse('project:project_list')
        response = self.client.get(
            url, {'q': '  aRdUiNo  ', 'tag': self.tag.slug},
        )
        self.assertEqual(list(response.context['projects']), [station])
        response = self.client.get(url, {'q': '100%'})
        self.assertEqual(list(response.context['projects']), [station])

    def test_catalog_invalid_query_keeps_form_and_shows_no_results(self):
        url = reverse('project:project_list')
        for query in ('x' * 101, 'x\x00'):
            with self.subTest(query=query):
                response = self.client.get(url, {'q': query})
                self.assertEqual(response.status_code, 200)
                self.assertIn('q', response.context['search_form'].errors)
                self.assertEqual(list(response.context['projects']), [])
        response = self.client.get(url, {'q': 'Несуществующий проект'})
        self.assertContains(response, 'Проекты не найдены.')
        self.assertContains(
            response,
            f'<a class="site-text-link" href="{url}">Сбросить фильтры '
            '<span aria-hidden="true">→</span></a>',
            html=True,
        )

    def test_catalog_pagination_keeps_filters_and_stable_order(self):
        items = Project.objects.bulk_create(
            [
                Project(
                    name=f'Arduino {index}',
                    slug=f'arduino-{index}',
                    user=self.owner,
                    document='station.pdf',
                )
                for index in range(PROJECTS_PER_PAGE + 2)
            ],
        )
        self.tag.projects.add(*items)
        Project.objects.filter(pk__in=[item.pk for item in items]).update(
            updated_at=self.project.updated_at,
        )
        expected = sorted(items, key=lambda item: item.pk, reverse=True)
        url = reverse('project:project_list')
        filters = {'q': 'Arduino', 'tag': self.tag.slug}

        response = self.client.get(url, {**filters, 'page': 'invalid'})
        self.assertEqual(list(response.context['projects']), expected[:-2])
        self.assertContains(
            response,
            f'q=Arduino&amp;tag={self.tag.slug}&amp;page=2',
        )
        response = self.client.get(url, {**filters, 'page': 999})
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertEqual(list(response.context['projects']), expected[-2:])
        self.assertContains(response, 'href="/project/?q=Arduino"')

    def test_creation_requires_authentication(self):
        login = reverse('authentication:login')
        self.assertRedirects(
            self.client.get(self.create_url),
            f'{login}?next={self.create_url}',
        )
        response = self.client.post(self.create_url, {'name': 'Без владельца'})
        self.assertRedirects(response, f'{login}?next={self.create_url}')
        self.assertEqual(Project.objects.count(), 1)

    def test_project_form_displays_tag_names(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.create_url)
        self.assertContains(response, self.tag.name)

    def test_reporting_requires_login_and_a_reason(self):
        url = self.project_url('project_report')
        self.assertContains(self.client.get(self.detail_url), url)
        login = reverse('authentication:login')
        self.assertRedirects(self.client.get(url), f'{login}?next={url}')
        self.assertRedirects(self.client.post(url), f'{login}?next={url}')

        self.client.force_login(self.reader)
        self.assertContains(self.client.get(url), 'Отправить жалобу')
        for reason in ('   ', 'x' * 1001):
            with self.subTest(reason=reason):
                response = self.client.post(url, {'reason': reason})
                self.assertIn('reason', response.context['form'].errors)
        self.assertFalse(ProjectReport.objects.exists())

    def test_one_pending_report_per_user_and_project(self):
        self.client.force_login(self.reader)
        url = self.project_url('project_report')
        reason = 'В проекте опубликован неверный документ.'
        response = self.client.post(url, {'reason': reason}, follow=True)
        self.assertRedirects(response, self.detail_url)
        self.assertContains(response, 'Жалоба отправлена модераторам.')
        report = ProjectReport.objects.get(project=self.project)
        self.assertEqual(report.reporter, self.reader)
        self.assertEqual(report.reason, reason)

        response = self.client.post(url, {'reason': 'Повтор'}, follow=True)
        self.assertContains(
            response,
            'Ваша жалоба уже ожидает рассмотрения.',
        )
        self.assertEqual(ProjectReport.objects.count(), 1)
        report.refresh_from_db()
        self.assertEqual(report.reason, reason)

    def test_only_moderators_can_read_and_resolve_reports(self):
        report = ProjectReport.objects.create(
            project=self.project,
            reporter=self.reader,
            reason='Причина жалобы',
        )
        queue_url = reverse('project:report_list')
        resolve_url = reverse('project:report_resolve', args=[report.pk])
        login = reverse('authentication:login')
        self.assertRedirects(
            self.client.get(queue_url),
            f'{login}?next={queue_url}',
        )
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(self.detail_url), queue_url)
        self.assertEqual(self.client.get(queue_url).status_code, 403)
        self.assertEqual(self.client.post(resolve_url).status_code, 403)
        report.refresh_from_db()
        self.assertIsNone(report.resolved_at)

        self.client.force_login(self.moderator)
        response = self.client.get(queue_url)
        self.assertContains(response, self.detail_url)
        self.assertContains(response, report.reason)
        self.assertEqual(self.client.get(resolve_url).status_code, 405)
        self.assertRedirects(self.client.post(resolve_url), queue_url)
        report.refresh_from_db()
        self.assertEqual(report.resolved_by, self.moderator)
        self.assertIsNotNone(report.resolved_at)
        self.assertNotContains(self.client.get(queue_url), report.reason)

        self.client.force_login(self.reader)
        response = self.client.post(
            self.project_url('project_report'),
            {'reason': 'Появилась другая проблема.'},
        )
        self.assertRedirects(response, self.detail_url)
        self.assertEqual(ProjectReport.objects.count(), 2)

    def test_creation_saves_owner_document_tags_and_gallery(self):
        other_tag = Tag.objects.create(name='Проектирование')
        project = self.create_project(
            user=self.reader.pk,
            tags=[self.tag.pk, other_tag.pk],
            main_image=self.png(),
            gallery=[
                self.png('Галерея-' + 'ф' * 45 + '.png'),
                self.png('b.png'),
            ],
        )
        self.assertEqual(project.user, self.owner)
        self.assertCountEqual(project.tags.all(), [self.tag, other_tag])
        self.assertTrue(project.document.storage.exists(project.document.name))
        document_url = self.project_url('project_document', project)
        self.client.logout()
        response = self.client.get(document_url)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(
            response['Content-Disposition'], 'inline; filename="document.pdf"',
        )
        self.assertEqual(
            b''.join(response.streaming_content),
            self.pdf().read(),
        )
        head = self.client.head(document_url)
        self.assertEqual(head['Content-Type'], 'application/pdf')
        self.assertEqual(
            head['Content-Disposition'], response['Content-Disposition'],
        )
        self.assertEqual(b''.join(head.streaming_content), b'')

        download = self.client.get(document_url, {'download': '1'})
        self.assertIn('attachment', download['Content-Disposition'])
        self.assertEqual(
            b''.join(download.streaming_content), self.pdf().read(),
        )
        detail = self.client.get(self.project_url('project_detail', project))
        self.assertContains(detail, 'Открыть PDF')
        self.assertContains(detail, project.main_image.main_image.url)
        self.assertContains(detail, 'Галерея')
        self.assertEqual(project.images.count(), 2)
        for image in project.images.all():
            self.assertTrue(image.image.storage.exists(image.image.name))
            self.assertContains(detail, image.image.url)
        catalog = self.client.get(reverse('project:project_list'))
        self.assertContains(catalog, '/media/cache/')

    def test_legacy_documents_are_downloaded_as_attachments(self):
        url = self.project_url('project_document')
        for name, content in (
            ('old-document.docx', b'old document'),
            ('invalid.pdf', b'<html>not a PDF</html>'),
        ):
            with self.subTest(name=name):
                upload = SimpleUploadedFile(name, content)
                self.project.document.save(name, upload)
                response = self.client.get(url)
                self.assertEqual(
                    response['Content-Type'], 'application/octet-stream',
                )
                self.assertIn('attachment', response['Content-Disposition'])
                self.assertEqual(b''.join(response.streaming_content), content)

    def test_missing_project_document_returns_not_found(self):
        response = self.client.get(self.project_url('project_document'))
        self.assertEqual(response.status_code, 404)

    def test_create_rejects_missing_or_invalid_document(self):
        self.client.force_login(self.owner)
        invalid_pdf = SimpleUploadedFile('document.pdf', b'plain text')
        for upload in (None, invalid_pdf):
            with self.subTest(upload=upload):
                data = {'name': 'Новый проект'}
                if upload is not None:
                    data['document'] = upload
                response = self.client.post(self.create_url, data)
                self.assertIn('document', response.context['form'].errors)
        self.assertEqual(Project.objects.count(), 1)

    def test_rejects_large_document_before_saving_files(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            self.create_url,
            {
                'name': 'Новый проект',
                'document': SimpleUploadedFile(
                    'large.pdf', b'%PDF-' + b'x' * MAX_DOCUMENT_SIZE,
                ),
            },
        )
        self.assertContains(response, 'Документ не должен превышать 10 МБ.')
        self.assertEqual(Project.objects.count(), 1)
        self.assertFalse(any(self.media.iterdir()))

    def test_rejects_invalid_image_format_size_and_dimensions(self):
        self.client.force_login(self.owner)
        for upload in (
            SimpleUploadedFile('a.png', b'not an image'),
            SimpleUploadedFile('a.png', b'x' * (MAX_IMAGE_SIZE + 1)),
            self.png('a.gif', image_format='GIF'),
            self.png(size=(4001, 4000)),
        ):
            with self.subTest(upload=upload):
                response = self.client.post(
                    self.create_url,
                    {'name': 'Новый проект', 'document': self.pdf(),
                     'main_image': upload},
                )
                self.assertIn('main_image', response.context['form'].errors)
        self.assertEqual(Project.objects.count(), 1)
        self.assertFalse(any(self.media.iterdir()))

    def test_rejects_invalid_or_oversized_gallery(self):
        self.client.force_login(self.owner)
        for uploads in (
            [self.png(), SimpleUploadedFile('bad.png', b'invalid')],
            [self.png() for _ in range(11)],
        ):
            with self.subTest(count=len(uploads)):
                response = self.client.post(
                    self.create_url,
                    {'name': 'Новый проект', 'document': self.pdf(),
                     'gallery': uploads},
                )
                self.assertIn('gallery', response.context['form'].errors)
        self.assertEqual(Project.objects.count(), 1)
        self.assertFalse(any(self.media.iterdir()))

    def test_owner_and_moderator_edits_preserve_legacy_document(self):
        edit_url = self.project_url('project_edit')
        for editor in (self.owner, self.moderator):
            with self.subTest(editor=editor):
                self.client.force_login(editor)
                self.assertContains(
                    self.client.get(edit_url),
                    'Редактировать проект',
                )
                self.assertContains(self.client.get(self.detail_url), edit_url)
                response = self.client.post(
                    edit_url,
                    {'name': editor.username},
                )
                self.assertRedirects(response, self.detail_url)
                self.project.refresh_from_db()
                self.assertEqual(self.project.name, editor.username)
                self.assertEqual(self.project.user, self.owner)
                self.assertEqual(
                    self.project.document.name,
                    'old-document.docx',
                )

    def test_unrelated_user_cannot_edit_or_delete(self):
        self.client.force_login(self.reader)
        for action in ('project_edit', 'project_delete'):
            url = self.project_url(action)
            self.assertEqual(self.client.get(url).status_code, 403)
            response = self.client.post(url, {'name': 'Изменено'})
            self.assertEqual(response.status_code, 403)
            self.assertNotContains(self.client.get(self.detail_url), url)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Робот')

    def test_edit_replaces_document_clears_cover_and_updates_gallery(self):
        project = self.create_project(
            main_image=self.png('cover.png'),
            gallery=[self.png('old.png')],
        )
        old_document = project.document
        old_cover = project.main_image.main_image
        old_image = project.images.get()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.project_url('project_edit', project),
                {
                    'name': project.name,
                    'document': self.pdf(),
                    'main_image-clear': 'on',
                    'gallery': [self.png('new.png')],
                    'remove_images': [old_image.pk],
                },
            )
        self.assertRedirects(
            response,
            self.project_url('project_detail', project),
        )
        project.refresh_from_db()
        self.assertFalse(hasattr(project, 'main_image'))
        self.assertTrue(project.images.get().image.name.endswith('/new.png'))
        for old_file in (old_document, old_cover, old_image.image):
            self.assertFalse(old_file.storage.exists(old_file.name))

    def test_upload_failure_rolls_back_rows_and_new_files(self):
        self.client.force_login(self.owner)
        error = OSError('storage failure')
        with patch.object(Image, 'save', side_effect=error):
            with self.assertRaises(OSError):
                self.client.post(
                    self.create_url,
                    {'name': 'Новый проект', 'document': self.pdf(),
                     'gallery': [self.png()]},
                )
        self.assertEqual(Project.objects.count(), 1)
        self.assertFalse(any(path.is_file() for path in self.media.rglob('*')))

    def test_moderator_can_delete_only_after_confirmation_post(self):
        project = self.create_project(gallery=[self.png()])
        self.client.force_login(self.moderator)
        url = self.project_url('project_delete', project)
        self.assertContains(self.client.get(url), 'Удалить проект')
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.assertRedirects(
                self.client.post(url),
                reverse('user:projects'),
            )
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        document = project.document
        self.assertFalse(document.storage.exists(document.name))
        self.assertFalse(Image.objects.filter(project=project).exists())

    def test_rating_requires_login_post_and_valid_value(self):
        url = self.project_url('project_rate')
        response = self.client.post(url, {'value': 4})
        login_url = reverse('authentication:login')
        self.assertRedirects(response, f'{login_url}?next={url}')
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(url).status_code, 405)
        for value in (0, 11, 'invalid'):
            with self.subTest(value=value):
                response = self.client.post(url, {'value': value})
                self.assertEqual(response.status_code, 400)
                self.assertIn('value', response.context['rating_form'].errors)
        self.assertFalse(Rating.objects.exists())

    def test_rating_update_recalculates_average_without_duplicates(self):
        url = self.project_url('project_rate')
        ratings = ((self.reader, 5), (self.reader, 9), (self.owner, 6))
        for user, value in ratings:
            self.client.force_login(user)
            response = self.client.post(url, {'value': value})
            self.assertRedirects(response, self.detail_url)
        self.assertEqual(self.project.ratings.count(), 2)
        self.assertEqual(self.project.ratings.get(user=self.reader).value, 9)
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Средняя оценка 7,5 из 10')
        self.assertEqual(response.context['rating_form'].initial, {'value': 6})


class ProjectAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            'admin', 'admin@example.test',
        )
        cls.owner = User.objects.create_user('author', 'author@example.test')
        cls.project = Project.objects.create(
            name='Метеостанция',
            user=cls.owner,
            document='old-document.pdf',
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_project_search_displays_existing_and_missing_cover(self):
        temp = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=Path(temp)))
        other = Project.objects.create(
            name='Карта парковок',
            user=self.owner,
            document='map.pdf',
        )
        MainImage.objects.create(
            project=self.project,
            main_image=ProjectTests.png('cover.png'),
        )
        Image.objects.create(
            project=self.project,
            image=ProjectTests.png('gallery.png'),
        )
        listing = reverse('admin:project_project_changelist')
        response = self.client.get(listing)
        self.assertContains(response, 'Нет изображения')
        self.assertContains(response, '<img src="/media/cache/')

        response = self.client.get(listing, {'q': self.project.name})
        self.assertContains(response, self.project.name)
        self.assertNotContains(response, other.name)
        url = reverse('admin:project_project_change', args=[self.project.pk])
        self.assertContains(self.client.get(url), '<img src="/media/cache/')

    def test_project_admin_rejects_non_pdf_document(self):
        response = self.client.post(
            reverse('admin:project_project_add'),
            {
                'name': 'Новый проект',
                'slug': 'new-project',
                'user': self.owner.pk,
                'document': SimpleUploadedFile('document.txt', b'not a PDF'),
            },
        )
        form = response.context['adminform'].form
        self.assertIn('document', form.errors)
        self.assertContains(response, 'Загрузите документ в формате PDF.')
        self.assertEqual(Project.objects.count(), 1)

    def test_admin_can_filter_and_resolve_reports_without_overwriting_audit(
        self,
    ):
        report = ProjectReport.objects.create(
            project=self.project,
            reporter=self.owner,
            reason='Уточнить данные проекта',
        )
        listing = reverse('admin:project_projectreport_changelist')
        pending = {'status': 'pending'}
        self.assertEqual(
            self.client.get(listing, pending).context['cl'].result_count, 1,
        )
        submission = {
            'action': 'resolve_reports',
            '_selected_action': report.pk,
            'index': 0,
        }
        self.assertRedirects(self.client.post(listing, submission), listing)
        report.refresh_from_db()
        self.assertEqual(report.resolved_by, self.admin)
        self.assertIsNotNone(report.resolved_at)
        resolved_at = report.resolved_at
        self.assertEqual(
            self.client.get(listing, pending).context['cl'].result_count, 0,
        )
        self.client.post(listing, submission)
        report.refresh_from_db()
        self.assertEqual(report.resolved_at, resolved_at)
