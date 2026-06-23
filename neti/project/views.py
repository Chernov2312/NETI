__all__ = ()
from django.shortcuts import render


def project_info(request):
    template = 'project/item_info.html'
    context = {}
    return render(request, template_name=template, context=context)
