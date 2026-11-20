__all__ = ()
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from user.models import User


class UserRegisterForm(UserCreationForm):

    email = forms.EmailField(label='Email')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    'class': 'form-control',
                    'placeholder': field.label,
                },
            )


class UserAuthorizationForm(forms.Form):
    login = forms.CharField(
        label='Логин или email',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите логин или email',
            },
        ),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите пароль',
            },
        ),
    )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        login = cleaned_data['login']
        user = User.objects.get_by_username(login)
        if user is None:
            user = User.objects.get_by_email(login)

        self.user = authenticate(
            self.request,
            username=user.username if user else login,
            password=cleaned_data['password'],
        )
        if self.user is None:
            raise forms.ValidationError('Неверный логин или пароль.')

        return cleaned_data
