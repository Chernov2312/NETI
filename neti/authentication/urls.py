__all__ = ()

from django.contrib.auth.views import (
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path, reverse_lazy

from authentication.views import login, registration

app_name = 'authentication'
reset_template = 'auth/password_reset.html'

urlpatterns = [
    path('login/', login, name='login'),
    path('registration/', registration, name='registration'),
    path('logout/', LogoutView.as_view(next_page='home:home'), name='logout'),
    path(
        'password-reset/',
        PasswordResetView.as_view(
            template_name=reset_template,
            email_template_name='auth/password_reset_email.txt',
            subject_template_name='auth/password_reset_subject.txt',
            success_url=reverse_lazy('authentication:password_reset_done'),
            extra_context={'submit_label': 'Отправить ссылку'},
        ),
        name='password_reset',
    ),
    path(
        'password-reset/sent/',
        PasswordResetDoneView.as_view(
            template_name=reset_template,
            extra_context={
                'message': 'Если на этот адрес зарегистрирован аккаунт, '
                'мы отправили письмо со ссылкой для сброса пароля.',
            },
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name=reset_template,
            success_url=reverse_lazy('authentication:password_reset_complete'),
            extra_context={'submit_label': 'Сохранить пароль'},
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        PasswordResetCompleteView.as_view(
            template_name=reset_template,
            extra_context={'message': 'Теперь можно войти с новым паролем.'},
        ),
        name='password_reset_complete',
    ),
]
