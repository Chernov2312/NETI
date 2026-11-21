__all__ = ()
from django.shortcuts import render

from project.models import Project


def home(request):
    return render(
        request,
        'homepage/home.html',
        {'recent_projects': Project.objects.get_projects_main()[:3]},
    )
