__all__ = ()
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from project.forms import ProjectForm, ProjectReportForm, RatingForm
from project.models import Project, ProjectReport, Rating, Tag


def project_list(request):
    projects = Project.objects.get_projects_main()
    tags = Tag.objects.order_by('name')
    selected_tag = None
    if slug := request.GET.get('tag'):
        selected_tag = get_object_or_404(tags, slug=slug)
        projects = projects.filter(tags=selected_tag)
    return render(
        request,
        'project/project_list.html',
        {
            'title': 'Каталог проектов',
            'projects': projects,
            'tags': tags,
            'selected_tag': selected_tag,
        },
    )


def project_detail(request, id):
    project = Project.objects.get_project_info(id)
    if project is None:
        raise Http404
    rating_form = None
    if request.user.is_authenticated:
        rating = project.ratings.filter(user=request.user).first()
        initial = {'value': rating.value} if rating else None
        rating_form = RatingForm(initial=initial)
    return render_detail(request, project, rating_form)


def render_detail(request, project, rating_form, status=200):
    return render(
        request,
        'project/item_info.html',
        {
            'project': project,
            'rating_form': rating_form,
            'can_manage': can_manage_project(request.user, project),
        },
        status=status,
    )


def can_manage_project(user, project):
    return user.is_authenticated and (
        user.pk == project.user_id or user.can_moderate_projects
    )


@require_http_methods(['GET', 'HEAD'])
def project_document(request, id):
    project = get_object_or_404(Project, id=id)
    try:
        document = project.document.open('rb')
    except (FileNotFoundError, ValueError) as error:
        raise Http404 from error
    return FileResponse(
        document,
        as_attachment=True,
        content_type='application/octet-stream',
    )


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
def project_create(request):
    project = Project(user=request.user)
    return project_form(request, project, 'Создать проект')


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
@transaction.atomic
def project_edit(request, id):
    project = get_object_or_404(Project.objects.select_for_update(), id=id)
    if not can_manage_project(request.user, project):
        raise PermissionDenied
    return project_form(request, project, 'Редактировать проект')


def project_form(request, project, title):
    is_edit = not project._state.adding
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save_project()
            return redirect('project:project_detail', id=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        'project/project_form.html',
        {'title': title, 'form': form, 'is_edit': is_edit},
    )


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
@transaction.atomic
def project_delete(request, id):
    project = get_object_or_404(Project.objects.select_for_update(), id=id)
    if not can_manage_project(request.user, project):
        raise PermissionDenied
    if request.method == 'POST':
        project.delete()
        return redirect('user:projects')
    return render(
        request,
        'project/project_confirm_delete.html',
        {'project': project},
    )


@login_required
@require_POST
@transaction.atomic
def project_rate(request, id):
    project = get_object_or_404(Project.objects.select_for_update(), id=id)
    form = RatingForm(request.POST)
    if form.is_valid():
        Rating.objects.update_or_create(
            project=project,
            user=request.user,
            defaults={'value': form.cleaned_data['value']},
        )
        return redirect('project:project_detail', id=id)
    project = Project.objects.get_project_info(id)
    return render_detail(request, project, form, status=400)


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
@transaction.atomic
def project_report(request, id):
    projects = Project.objects.all()
    if request.method == 'POST':
        projects = projects.select_for_update()
    project = get_object_or_404(projects, pk=id)

    form = ProjectReportForm(
        request.POST if request.method == 'POST' else None,
    )
    if form.is_valid():
        _, created = ProjectReport.objects.get_or_create(
            project=project,
            reporter=request.user,
            resolved_at__isnull=True,
            defaults={'reason': form.cleaned_data['reason']},
        )
        if created:
            messages.success(request, 'Жалоба отправлена модераторам.')
        else:
            messages.info(request, 'Ваша жалоба уже ожидает рассмотрения.')
        return redirect('project:project_detail', id=project.pk)

    return render(
        request,
        'project/project_report.html',
        {'project': project, 'form': form},
    )


@login_required
@require_http_methods(['GET', 'HEAD'])
def report_list(request):
    if not request.user.can_moderate_projects:
        raise PermissionDenied
    reports = (
        ProjectReport.objects.filter(resolved_at__isnull=True)
        .select_related('project', 'reporter')
        .order_by('created_at', 'pk')
    )
    return render(request, 'project/report_list.html', {'reports': reports})


@login_required
@require_POST
def report_resolve(request, id):
    if not request.user.can_moderate_projects:
        raise PermissionDenied
    report = get_object_or_404(ProjectReport, pk=id)
    ProjectReport.objects.filter(pk=report.pk).resolve(request.user)
    return redirect('project:report_list')
