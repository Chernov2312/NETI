__all__ = ()

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import User


@admin.register(User)
class NetiUserAdmin(UserAdmin):
    fieldsets = (
        *UserAdmin.fieldsets,
        ('Роль в каталоге', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'role',
                    'usable_password',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
    list_display = (*UserAdmin.list_display, 'role')
    list_filter = (*UserAdmin.list_filter, 'role')

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
