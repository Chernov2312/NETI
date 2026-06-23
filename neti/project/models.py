__all__ = ()
from autoslug import AutoSlugField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import NameBaseModel, UpdateBaseModel
from project.utils import save_file_path_document, save_file_path_image


class Tags(UpdateBaseModel, NameBaseModel):
    slug = AutoSlugField(populate_from='name', unique=True, editable=True)


class Project(UpdateBaseModel, NameBaseModel):
    description = models.CharField(
        max_length=1000,
        verbose_name=_('Описание'),
        null=True,
        blank=True,
    )
    document = models.FileField(
        upload_to=save_file_path_document,
        blank=False,
        null=False,
    )
    user = models.ForeignKey(
        'user.User',
        verbose_name=_('разработчик'),
        on_delete=models.CASCADE,
        related_name='projects',
    )
    tags = models.ManyToManyField(
        Tags,
        related_name='projects',
        verbose_name='теги',
        blank=True,
        related_query_name='project',
    )
    slug = AutoSlugField(populate_from='name', unique=True, editable=True)


class Rating(models.Model):
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    user = models.ForeignKey(
        'user.User',
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    value = models.PositiveSmallIntegerField(
        verbose_name=_('Оценка'),
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    class Meta:
        unique_together = ('project', 'user')
        verbose_name = _('Рейтинг')
        verbose_name_plural = _('Рейтинги')


class Image(UpdateBaseModel):
    image = models.ImageField(
        upload_to=save_file_path_image,
        null=True,
    )
    project = models.ForeignKey(
        'Project',
        verbose_name=_('дополнительное изображение'),
        on_delete=models.CASCADE,
        related_name='images',
    )


class MainImage(UpdateBaseModel):
    main_image = models.ImageField(
        upload_to=save_file_path_image,
        null=False,
    )
    project = models.OneToOneField(
        'Project',
        verbose_name=_('главное изображение'),
        on_delete=models.CASCADE,
        related_name='main_image',
    )
