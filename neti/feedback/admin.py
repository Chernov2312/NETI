__all__ = ()

from urllib.parse import quote

from django.contrib import admin
from django.utils.html import format_html

from feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'message')
    ordering = ('-created_at',)
    readonly_fields = (
        'name', 'email', 'message', 'created_at', 'updated_at', 'reply_link',
    )
    fields = (
        'name', 'email', 'message', 'created_at', 'updated_at',
        'status', 'note', 'reply_link',
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description='Ответить отправителю')
    def reply_link(self, obj):
        return format_html(
            '<a href="mailto:{}">Открыть почтовую программу</a>',
            quote(obj.email, safe='@'),
        )
