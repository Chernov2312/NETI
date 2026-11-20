__all__ = ()

from django.urls import path

from project import views

app_name = 'project'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('detail/<uuid:id>/', views.project_detail, name='project_detail'),
    path(
        '<uuid:id>/document/',
        views.project_document,
        name='project_document',
    ),
    path('<uuid:id>/edit/', views.project_edit, name='project_edit'),
    path('<uuid:id>/delete/', views.project_delete, name='project_delete'),
    path('<uuid:id>/rate/', views.project_rate, name='project_rate'),
    path('<uuid:id>/report/', views.project_report, name='project_report'),
    path('reports/', views.report_list, name='report_list'),
    path(
        'reports/<int:id>/resolve/',
        views.report_resolve,
        name='report_resolve',
    ),
]
