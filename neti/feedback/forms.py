__all__ = ()

from django import forms

from feedback.models import Feedback


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('name', 'email', 'message')
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'name'},
            ),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'autocomplete': 'email'},
            ),
            'message': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5},
            ),
        }
