__all__ = ()
from django.contrib.auth import login as auth_login
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from authentication.forms import UserAuthorizationForm, UserRegisterForm


def registration(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except (IntegrityError, ValidationError):
                # Another registration may have saved the login or email.
                form.full_clean()
                if not form.errors:
                    raise
            else:
                return redirect('authentication:login')
        form.fields['username'].widget.attrs.pop('autofocus', None)
    else:
        form = UserRegisterForm()
    template = 'auth/auth.html'
    context = {
        'form': form,
        'title': 'Регистрация',
    }
    return render(request, template_name=template, context=context)


def login(request):
    next_url = request.POST.get('next', request.GET.get('next', ''))
    if request.method == 'POST':
        form = UserAuthorizationForm(request.POST, request=request)
        if form.is_valid():
            auth_login(request, form.user)
            if url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('project:project_list')
    else:
        form = UserAuthorizationForm()
    template = 'auth/auth.html'
    context = {
        'form': form,
        'title': 'Вход',
        'next': next_url,
    }
    return render(request, template_name=template, context=context)
