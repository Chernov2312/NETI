__all__ = ()

import re
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from playwright.sync_api import expect, sync_playwright


@override_settings(
    DEBUG=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ProjectBrowserTests(StaticLiveServerTestCase):
    demo = settings.BASE_DIR.parent / 'demo'
    fixtures = [str(demo / 'neti-demo.json')]
    demo_password = 'DemoNeti-Only!26'
    station_name = 'Мини-метеостанция'
    parking_name = 'Карта велопарковок'

    def setUp(self):
        temp = Path(self.enterContext(TemporaryDirectory()))
        media = temp / 'media'
        copytree(self.demo / 'files', media)
        self.enterContext(override_settings(MEDIA_ROOT=media))

        playwright = self.enterContext(sync_playwright())
        browser = playwright.chromium.launch()
        self.addCleanup(browser.close)
        self.page = browser.new_page(base_url=self.live_server_url)
        self.addCleanup(self.page.close)
        self.page.set_default_timeout(10000)

    def login(self, identifier, password=None):
        self.page.goto(reverse('authentication:login'))
        self.page.get_by_label('Логин или email').fill(identifier)
        self.page.get_by_label('Пароль', exact=True).fill(
            password or self.demo_password,
        )
        self.page.get_by_role('button', name='Войти', exact=True).click()
        expect(self.page.get_by_role('link', name='Профиль')).to_be_visible()

    def logout(self):
        self.page.get_by_role('button', name='Выйти', exact=True).click()
        expect(self.page.get_by_role('link', name='Войти')).to_be_visible()

    def open_project(self, name):
        card = self.page.locator('.card').filter(
            has=self.page.get_by_role('heading', name=name, exact=True),
        )
        card.get_by_role('link', name='Открыть проект').click()

    def test_register_and_manage_project_with_attachments(self):
        page = self.page
        password = 'Project-Author-Only!26'
        page.goto(reverse('authentication:login'))
        page.get_by_role('link', name='Зарегистрироваться').click()
        page.locator('[name="username"]').fill('e2e_author')
        page.get_by_label('Email', exact=True).fill('e2e.author@example.test')
        page.locator('[name="password1"]').fill(password)
        page.locator('[name="password2"]').fill(password)
        page.get_by_role('button', name='Зарегистрироваться').click()
        expect(page.get_by_role('button', name='Войти')).to_be_visible()

        self.login('e2e.author@example.test', password)
        page.get_by_role('link', name='Создать проект').click()
        name = 'Станция мониторинга кампуса'
        page.get_by_label('Название').fill(name)
        page.get_by_label('Описание').fill('Начальное описание станции')

        demo_files = self.demo / 'files' / 'neti-demo'
        pdf = demo_files / 'weather-station.pdf'
        page.get_by_label('Документ').set_input_files(pdf)
        page.get_by_label('Главное изображение').set_input_files(
            demo_files / 'weather-station.png',
        )
        page.get_by_label('Добавить изображения в галерею').set_input_files(
            demo_files / 'weather-readings.png',
        )
        page.get_by_role('checkbox', name='Электроника').check()
        page.get_by_role('button', name='Сохранить', exact=True).click()

        expect(page.get_by_role('heading', name=name)).to_be_visible()
        expect(page.get_by_role('link', name='#Электроника')).to_be_visible()
        photo = page.get_by_alt_text(f'Изображение проекта {name}')
        photo.scroll_into_view_if_needed()
        expect(photo).to_have_js_property('naturalWidth', 540)
        with page.expect_download() as download:
            page.get_by_role('link', name='Скачать документ').click()
        self.assertEqual(download.value.path().read_bytes(), pdf.read_bytes())

        page.get_by_role('link', name='Редактировать').click()
        page.get_by_label('Описание').fill('Описание после редактирования')
        page.get_by_role('button', name='Сохранить', exact=True).click()
        description = page.get_by_text('Описание после редактирования')
        expect(description).to_be_visible()
        page.get_by_role('link', name='Мои проекты').click()
        self.open_project(name)
        page.get_by_role('link', name='Удалить', exact=True).click()
        page.get_by_role('button', name='Удалить проект').click()
        expect(page.get_by_role('heading', name='Мои проекты')).to_be_visible()
        expect(page.get_by_role('heading', name=name)).to_have_count(0)
        self.logout()

    def test_filter_catalog_and_replace_rating(self):
        page = self.page
        self.login('demo_moderator')
        page.get_by_role('link', name='Электроника', exact=True).click()
        station = page.get_by_role('heading', name=self.station_name)
        parking = page.get_by_role('heading', name=self.parking_name)
        expect(station).to_be_visible()
        expect(parking).to_have_count(0)
        self.open_project(self.station_name)

        rating = page.get_by_role('spinbutton', name='Ваша оценка')
        expect(rating).to_have_value('8')
        rating.fill('6')
        page.get_by_role('button', name='Сохранить оценку').click()
        expect(rating).to_have_value('6')
        average = page.get_by_text(re.compile(r'Средняя оценка 6[,.]0 из 10'))
        expect(average).to_be_visible()

    def test_report_queue_and_moderator_permissions(self):
        page = self.page
        self.login('demo_student')
        expect(page.get_by_role('link', name='Жалобы')).to_have_count(0)
        response = page.goto(reverse('project:report_list'))
        self.assertEqual(response.status, 403)
        page.goto(reverse('project:project_list'))
        self.open_project(self.parking_name)
        page.get_by_role('link', name='Пожаловаться').click()
        page.get_by_label('Причина').fill('Повтор исходной жалобы')
        page.get_by_role('button', name='Отправить жалобу').click()
        expect(page.get_by_role('status')).to_have_text(
            'Ваша жалоба уже ожидает рассмотрения.',
        )

        self.logout()
        self.login('demo_moderator')
        page.get_by_role('link', name='Жалобы', exact=True).click()
        project_link = page.get_by_role('link', name=self.parking_name)
        expect(project_link).to_be_visible()
        resolve_button = page.get_by_role(
            'button',
            name='Отметить как рассмотренную',
        )
        resolve_button.click()
        empty_queue = page.get_by_text('Жалоб, ожидающих рассмотрения, нет.')
        expect(empty_queue).to_be_visible()

        self.logout()
        self.login('demo_student')
        self.open_project(self.parking_name)
        page.get_by_role('link', name='Пожаловаться').click()
        page.get_by_label('Причина').fill('Нужен актуальный адрес парковки')
        page.get_by_role('button', name='Отправить жалобу').click()
        expect(page.get_by_role('status')).to_have_text(
            'Жалоба отправлена модераторам.',
        )

    def test_reset_password_from_email(self):
        page = self.page
        page.goto(reverse('authentication:login'))
        page.get_by_role('link', name='Забыли пароль?').click()
        page.locator('input[name="email"]').fill('demo.student@example.test')
        page.get_by_role('button', name='Отправить ссылку').click()
        sent = page.get_by_text('мы отправили письмо', exact=False)
        expect(sent).to_be_visible()

        self.assertEqual(len(mail.outbox), 1)
        lines = mail.outbox[0].body.splitlines()
        origin = self.live_server_url + '/'
        link = next(line for line in lines if line.startswith(origin))
        page.goto(link)
        new_password = 'New-E2E-Password!26'
        page.locator('[name="new_password1"]').fill(new_password)
        page.locator('[name="new_password2"]').fill(new_password)
        page.get_by_role('button', name='Сохранить пароль').click()
        complete = page.get_by_text('Теперь можно войти с новым паролем.')
        expect(complete).to_be_visible()
        self.login('demo_student', new_password)
        page.goto(link)
        retry = page.get_by_role('link', name='Запросить новую ссылку')
        expect(retry).to_be_visible()

    def test_guest_submits_feedback(self):
        page = self.page
        page.goto(reverse('home:home'))
        page.get_by_role('link', name='Обратная связь', exact=True).click()
        page.get_by_label('Имя').fill('Анна')
        page.get_by_label('Email').fill('anna@example.test')
        page.get_by_label('Сообщение').fill('Добавьте поиск по автору.')
        page.get_by_role('button', name='Отправить обращение').click()
        expect(page.get_by_role('status')).to_have_text(
            'Ваше обращение отправлено.',
        )
