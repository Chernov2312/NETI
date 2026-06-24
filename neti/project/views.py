__all__ = ()
from uuid import UUID

from django.shortcuts import render

from project.models import Project


def project_list(request):
    template = 'project/project_list.html'
    context = {'projects': Project.objects.get_projects_main()}
    return render(request, template_name=template, context=context)


def project_detail(request, id: UUID):
    template = 'project/item_info.html'
    context = {'project': Project.objects.get_project_info(id)}
    return render(request, template_name=template, context=context)
