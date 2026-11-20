# Инструкции для AI-агентов

## О проекте

NETI — Django-приложение на русском языке: каталог проектов с регистрацией
пользователей, тегами, изображениями и оценками. Основной код Django находится
в каталоге `neti/`, настройки — в `neti/neti/settings.py`.

## Структура репозитория

- `neti/authentication/` — формы и представления регистрации и входа.
- `neti/core/` — абстрактные модели с UUID, датами, именем и обработкой
  изображений.
- `neti/home/` — главная страница.
- `neti/project/` — проекты, теги, рейтинги, изображения, менеджер,
  административная часть и миграции.
- `neti/user/` — пользовательская модель, менеджер, валидатор ролей и профиль.
- `neti/neti/` — настройки, корневые URL, ASGI и WSGI.
- `neti/templates/` — Django-шаблоны.
- `neti/static_dev/` — статические CSS и JS.
- `requirements/` — зависимости приложения, разработки и тестов.
- `Dockerfile`, `docker-compose.yml` — конфигурация контейнеров.

## Модели и схема данных

Модели и миграции — источник истины для схемы. Не изменяйте схему БД вручную:
меняйте Django-модели, создавайте миграции и проверяйте их.

- `user_user` (`user.User`, UUID PK): наследует поля Django `AbstractUser`
  (`password`, `last_login`, `is_superuser`, `first_name`, `last_name`,
  `is_staff`, `is_active`, `date_joined`, `groups`,
  `user_permissions`) и добавляет `created_at`, `updated_at`, уникальные
  `username` и `email`, `role` (`student` или `moderator`). У пользователя
  много проектов и рейтингов. Поле `role` не является отдельной моделью.
- `project_project` (`project.Project`, UUID PK): `created_at`, `updated_at`,
  уникальные `name` и `slug`, `description` (до 1000 символов), обязательный
  `document`, FK `user_id` на пользователя с `CASCADE`. Есть M2M-связь с
  тегами через промежуточную таблицу Django `project_project_tags`.
- `project_tag` (`project.Tag`, UUID PK): `created_at`, `updated_at`,
  уникальные `name` и `slug`.
- `project_rating` (`project.Rating`, BigAutoField PK): FK `project_id` и
  `user_id` с `CASCADE`, `value` от 1 до 10. Уникальная пара проекта и
  пользователя: один пользователь может оставить одну оценку проекту.
- `project_image` (`project.Image`, UUID PK): `created_at`, `updated_at`,
  необязательное изображение и FK `project_id` с `CASCADE`.
- `project_mainimage` (`project.MainImage`, UUID PK): `created_at`,
  `updated_at`, обязательное главное изображение и уникальный FK `project_id`
  (OneToOne) с `CASCADE`.

`UpdateBaseModel`, `NameBaseModel` и `ImageBaseModel` — абстрактные модели;
отдельных таблиц для них нет. Связанные изображения и документы хранятся в
`MEDIA_ROOT`, а не в БД. Дополнительные поля `groups` и `user_permissions`
создают стандартные M2M-таблицы Django.

## Правила разработки

- Перед изменениями изучите существующие модели, URL, шаблоны и миграции.
- Сохраняйте текущие Django-паттерны и локализацию; не добавляйте зависимости
  без необходимости.
- Для изменений моделей добавляйте миграцию и не редактируйте уже применённые
  миграции без явной причины.
- Для новых/изменённых пользовательских сценариев добавляйте тесты в
  `tests.py` соответствующего приложения.
- Не предполагайте, что поля или маршруты существуют: сверяйтесь с моделями,
  URLconf и шаблонами.
- Не помещайте секреты в исходники. Локальные настройки задаются через `.env`.

## Локальная разработка (Windows)

Из корня репозитория:

```powershell
.\.venv\Scripts\Activate.ps1
python neti\manage.py runserver
python neti\manage.py check
python neti\manage.py makemigrations --check --dry-run
python neti\manage.py test
```

Для окружения с тестовыми и lint-зависимостями установите
`requirements/test.txt`; он включает `requirements/dev.txt` и
`requirements/prod.txt`.

## Конфигурация БД

Django и Compose по умолчанию используют PostgreSQL. Для локального запуска
создайте `.env` по `.env.example` и задайте значения `POSTGRES_*`.
Для тестов на SQLite и экспорта прежней базы задайте `DJANGO_DB_ENGINE=sqlite`.
Инструкция переноса данных и медиа находится в README.
