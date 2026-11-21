__all__ = ()
import uuid

from django.db import models
from django.utils.html import format_html
from sorl.thumbnail import get_thumbnail


class UpdateBaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        abstract = True


class NameBaseModel(models.Model):
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        unique=True,
    )

    class Meta:
        abstract = True


class ImageBaseModel(models.Model):
    class Meta:
        abstract = True

    def get_image_300x300(self):
        thumbnail = self.get_from_model('300x300', crop='center', quality=85)
        return thumbnail.url if thumbnail else None

    def get_image_tmb(self, width=50, height=50):
        try:
            thumbnail = self.get_from_model(f'{width}x{height}', crop='center')
        except (OSError, ValueError):
            return 'Ошибка загрузки'
        if not thumbnail:
            return 'Нет изображения'
        return format_html(
            '<img src="{}" width="{}" height="{}" '
            'style="object-fit: cover;" alt="">',
            thumbnail.url,
            width,
            height,
        )

    get_image_tmb.short_description = 'Миниатюра'

    def get_from_model(self, geometry_string, **options):
        source = self._available_image()
        if source is None:
            return None

        try:
            thumbnail = get_thumbnail(source, geometry_string, **options)
        except FileNotFoundError:
            return None
        return thumbnail if thumbnail and thumbnail.exists() else None

    def get_image_url(self):
        source = self._available_image()
        return source.url if source else None

    def _available_image(self):
        source = getattr(self, 'image', None) or getattr(
            self,
            'main_image',
            None,
        )
        if source and source.storage.exists(source.name):
            return source
        return None
