__all__ = ()
from autoslug import AutoSlugField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import ImageBaseModel, NameBaseModel, UpdateBaseModel
from project.managers import ProjectManager, ProjectReportQuerySet
from project.utils import save_file_path_document, save_file_path_image


class Tag(UpdateBaseModel, NameBaseModel):
    slug = AutoSlugField(populate_from='name', unique=True, editable=True)

    class Meta:
        verbose_name = _('тег')
        verbose_name_plural = _('теги')

    def __str__(self):
        return self.name


class Project(UpdateBaseModel, NameBaseModel):
    objects = ProjectManager()
    description = models.CharField(
        max_length=1000,
        verbose_name=_('Описание'),
        null=True,
        blank=True,
    )
    document = models.FileField(
        upload_to=save_file_path_document,
        max_length=500,
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
        Tag,
        related_name='projects',
        verbose_name='теги',
        blank=True,
        related_query_name='project',
    )
    slug = AutoSlugField(populate_from='name', unique=True, editable=True)

    class Meta:
        verbose_name = _('проект')
        verbose_name_plural = _('проекты')
        indexes = [
            models.Index(
                fields=('-updated_at', '-id'),
                name='project_updated_id_idx',
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def document_is_pdf(self):
        return (self.document.name or '').lower().endswith('.pdf')


class Opportunity(UpdateBaseModel, models.Model):
    class Kind(models.TextChoices):
        BRIEF = 'brief', _('Техническое задание')
        IDEA = 'idea', _('Идея проекта')

    title = models.CharField(max_length=160, verbose_name=_('Название'))
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.BRIEF,
        verbose_name=_('Тип предложения'),
    )
    organization = models.CharField(
        max_length=160,
        verbose_name=_('Вуз или организация'),
    )
    description = models.TextField(
        max_length=5000,
        verbose_name=_('Описание и требования'),
    )
    contact_email = models.EmailField(verbose_name=_('Email для связи'))
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Срок выполнения'),
    )
    author = models.ForeignKey(
        'user.User',
        on_delete=models.CASCADE,
        related_name='opportunities',
        verbose_name=_('Представитель вуза'),
    )

    class Meta:
        ordering = ('-created_at', '-id')
        verbose_name = _('задание биржи')
        verbose_name_plural = _('задания биржи')

    def __str__(self):
        return self.title


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


class ProjectReport(models.Model):
    objects = ProjectReportQuerySet.as_manager()
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    reporter = models.ForeignKey(
        'user.User',
        on_delete=models.CASCADE,
        related_name='project_reports',
    )
    reason = models.CharField(max_length=1000, verbose_name=_('Причина'))
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'user.User',
        on_delete=models.SET_NULL,
        related_name='resolved_project_reports',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('жалоба на проект')
        verbose_name_plural = _('жалобы на проекты')
        constraints = [
            models.UniqueConstraint(
                fields=('project', 'reporter'),
                condition=models.Q(resolved_at__isnull=True),
                name='unique_pending_project_report',
            ),
        ]


class Image(UpdateBaseModel, ImageBaseModel):
    image = models.ImageField(
        upload_to=save_file_path_image,
        max_length=255,
        null=True,
    )
    project = models.ForeignKey(
        'Project',
        verbose_name=_('дополнительное изображение'),
        on_delete=models.CASCADE,
        related_name='images',
    )

    class Meta:
        verbose_name = _('изображение галереи')
        verbose_name_plural = _('изображения галереи')


class MainImage(UpdateBaseModel, ImageBaseModel):
    main_image = models.ImageField(
        upload_to=save_file_path_image,
        max_length=255,
        null=False,
    )
    project = models.OneToOneField(
        'Project',
        verbose_name=_('главное изображение'),
        on_delete=models.CASCADE,
        related_name='main_image',
    )

    class Meta:
        verbose_name = _('главное изображение')
        verbose_name_plural = _('главные изображения')

    def get_wide_thumbnail(self):
        return self.get_from_model('640x320', crop='center', quality=85)
