from django.urls import path

from project.views import project_detail, project_list

app_name = 'project'

urlpatterns = [
    path('', project_list, name='project_list'),
    path('detail/<uuid:id>/', project_detail, name='project_detail'),
]
