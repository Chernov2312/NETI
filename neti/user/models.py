__all__ = ()
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import UpdateBaseModel
from user.validators import RoleValidate


class User(AbstractUser, UpdateBaseModel):
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
        default='student',
        validators=[RoleValidate()],
        verbose_name=_('Роль'),
    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
