from django.urls import path

from user.views import profile

app_name = 'user'

urlpatterns = [
    path('me/', profile, name='profile'),
]
