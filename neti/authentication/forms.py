__all__ = ()
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UsernameField

from user.models import User


class UserRegisterForm(UserCreationForm):
    username = UsernameField(
        label='Имя пользователя',
        max_length=150,
        help_text='До 150 символов.',
        error_messages={'unique': 'Это имя пользователя уже занято.'},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
        labels = {'email': 'Email'}
        widgets = {'email': forms.EmailInput(attrs={'autocomplete': 'email'})}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Этот адрес электронной почты уже используется.',
                code='unique',
            )
        return email


class UserAuthorizationForm(forms.Form):
    login = forms.CharField(
        label='Логин или email',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'username',
            },
        ),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'current-password',
            },
        ),
    )

    def __init__(self, *args, request=None, **kwargs):
        kwargs.setdefault('label_suffix', '')
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
