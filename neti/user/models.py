__all__ = ()
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import UpdateBaseModel
from user.managers import UserManager


class User(AbstractUser, UpdateBaseModel):
    class Role(models.TextChoices):
        STUDENT = 'student', _('Студент')
        MODERATOR = 'moderator', _('Модератор')

    objects = UserManager()
    username = models.CharField(
        unique=True,
        null=False,
    )
    email = models.EmailField(
        unique=True,
        null=False,
        blank=False,
    )
    role = models.CharField(
        max_length=30,
        null=False,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name=_('Роль'),
    )

    @property
    def can_moderate_projects(self):
        return self.is_superuser or self.role == self.Role.MODERATOR

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
