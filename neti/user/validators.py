__all__ = ()
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class RoleValidate:
    def __init__(self):
        self.message = _('Указана несуществующая роль пользователя')

    def __call__(self, value):
        if value not in ['student', 'moderator']:
            raise ValidationError(self.message, code='invalid')
