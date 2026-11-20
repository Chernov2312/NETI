__all__ = ()

from django.urls import path

from feedback.views import feedback_form

app_name = 'feedback'

urlpatterns = [
    path('', feedback_form, name='form'),
]
