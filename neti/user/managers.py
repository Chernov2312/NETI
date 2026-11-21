__all__ = ()
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def _base_queryset(self):
        queryset = self.get_queryset()
        return queryset

    def get_by_username(self, username: str):
        return self._base_queryset().filter(username=username).first()

    def get_by_email(self, email: str):
        queryset = self._base_queryset()
        exact_match = queryset.filter(email=email).first()
        if exact_match is not None:
            return exact_match

        matches = list(queryset.filter(email__iexact=email)[:2])
        return matches[0] if len(matches) == 1 else None

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Поле Email должно быть заполнено')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_superuser=True.',
            )

        return self.create_user(username, email, password, **extra_fields)
