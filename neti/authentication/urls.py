from authentication.views import login, registration
from django.urls import path

app_name = 'authentication'

urlpatterns = [
    path('login/', login, name='login'),
    path('registration/', registration, name='registration'),
]
