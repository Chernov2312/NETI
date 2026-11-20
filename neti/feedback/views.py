__all__ = ()

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from feedback.forms import FeedbackForm


@require_http_methods(['GET', 'HEAD', 'POST'])
def feedback_form(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ваше обращение отправлено.')
            return redirect('feedback:form')
    else:
        initial = None
        if request.user.is_authenticated:
            initial = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
        form = FeedbackForm(initial=initial)

    return render(request, 'feedback/form.html', {'form': form})
