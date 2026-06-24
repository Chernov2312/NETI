__all__ = ()
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile(request):
    user = request.user
    template = 'user/profile.html'
    context = {'user': user}
    return render(request=request, template_name=template, context=context)
