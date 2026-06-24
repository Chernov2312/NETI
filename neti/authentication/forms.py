__all__ = ()
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import check_password

from user.models import User


class UserRegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for _, field in self.fields.items():
            field.widget.attrs.update(
                {
                    'class': 'form-control',
                    'placeholder': field.label,
                },
            )


class UserAuthorizationForm(forms.Form):
    login = forms.CharField(
        label='Логин или email',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите логин или email',
            },
        ),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите пароль',
            },
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        login_value = cleaned_data.get('login')
        password_value = cleaned_data.get('password')

        user = User.objects.get_by_username(login_value)
        if user is None:
            user = User.objects.get_by_email(login_value)
        invalid_credentials_message = 'Неверный логин или пароль.'

        if user is None or not check_password(password_value, user.password):
            raise forms.ValidationError(invalid_credentials_message)

        self.user = user
        return cleaned_data
