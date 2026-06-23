__all__ = ()
from django.shortcuts import render


def home(request):
    template = 'homepage/home.html'
    context = {}
    return render(request, template_name=template, context=context)
