__all__ = ()

from django.urls import path

from user.views import profile, projects

app_name = 'user'

urlpatterns = [
    path('me/', profile, name='profile'),
    path('me/projects/', projects, name='projects'),
]
