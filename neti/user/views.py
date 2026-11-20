__all__ = ()
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from project.models import Project


@login_required
def profile(request):
    return render(request, 'user/profile.html', {'profile_user': request.user})


@login_required
def projects(request):
    return render(
        request,
        'project/project_list.html',
        {
            'title': 'Мои проекты',
            'projects': Project.objects.get_projects_main().filter(
                user=request.user,
            ),
        },
    )
