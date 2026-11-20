__all__ = ()

from django.db import models

from core.models import UpdateBaseModel


class Feedback(UpdateBaseModel):
    class Status(models.TextChoices):
        NEW = 'new', 'Новое'
        IN_PROGRESS = 'in_progress', 'В работе'
        CLOSED = 'closed', 'Закрыто'

    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    message = models.TextField('Сообщение', max_length=2000)
    status = models.CharField(
        'Статус',
        max_length=11,
        choices=Status.choices,
        default=Status.NEW,
    )
    note = models.TextField('Заметка сотрудника', blank=True, max_length=2000)

    class Meta:
        verbose_name = 'обращение'
        verbose_name_plural = 'обращения'

    def __str__(self):
        return f'{self.name} ({self.email})'
