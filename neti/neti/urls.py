from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Администрирование NETI'
admin.site.site_title = 'NETI'
admin.site.index_title = 'Управление каталогом'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('project/', include('project.urls')),
    path('auth/', include('authentication.urls')),
    path('feedback/', include('feedback.urls')),
    path('user/', include('user.urls')),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
