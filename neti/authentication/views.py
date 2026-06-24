__all__ = ()
from authentication.forms import UserAuthorizationForm, UserRegisterForm
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render


def registration(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('authentication:login')
    else:
        form = UserRegisterForm()
    template = 'auth/auth.html'
    context = {
        'form': form,
        'title': 'Регистрация',
    }
    return render(request, template_name=template, context=context)


def login(request):
    if request.method == 'POST':
        form = UserAuthorizationForm(request.POST)
        if form.is_valid():
            user = form.user
            auth_login(request, user)
            return redirect('project:project_list')
    template = 'auth/auth.html'
    context = {
        'form': UserAuthorizationForm(),
        'title': 'Вход',
    }
    return render(request, template_name=template, context=context)
