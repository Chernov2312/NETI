__all__ = ()
from django.contrib import admin
from django.db import models

from project.forms import DocumentField, ProjectImageField
from project.inlines import ImageInline, MainImageInline
from project.models import (
    Image,
    MainImage,
    Opportunity,
    Project,
    ProjectReport,
    Rating,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'value')
    list_filter = ('value', 'project')
    list_select_related = ('project', 'user')
    search_fields = ('project__name', 'user__username')


class ProjectImageAdmin(admin.ModelAdmin):
    list_select_related = ('project',)
    list_filter = ('project', 'created_at')
    search_fields = ('project__name',)
    readonly_fields = ('get_image_tmb',)
    formfield_overrides = {
        models.ImageField: {'form_class': ProjectImageField},
    }


@admin.register(Image)
class ImageAdmin(ProjectImageAdmin):
    list_display = ('project', 'image', 'get_image_tmb')


@admin.register(MainImage)
class MainImageAdmin(ProjectImageAdmin):
    list_display = ('project', 'main_image', 'get_image_tmb')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = (MainImageInline, ImageInline)
    list_display = ('name', 'user', 'cover_preview', 'updated_at')
    list_filter = ('tags', 'updated_at')
    list_select_related = ('user', 'main_image')
    search_fields = ('name', 'description', 'user__username')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    formfield_overrides = {models.FileField: {'form_class': DocumentField}}

    @admin.display(description='Главное изображение')
    def cover_preview(self, obj):
        cover = getattr(obj, 'main_image', None)
        return cover.get_image_tmb() if cover else 'Нет изображения'


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'kind', 'author', 'created_at')
    list_filter = ('kind', 'created_at')
    search_fields = (
        'title', 'organization', 'description', 'author__username',
    )
    readonly_fields = ('created_at', 'updated_at')


class ReportStatusFilter(admin.SimpleListFilter):
    title = 'статус'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Ожидают рассмотрения'),
            ('resolved', 'Рассмотрены'),
        )

    def queryset(self, request, queryset):
        status = self.value()
        if status in ('pending', 'resolved'):
            return queryset.filter(resolved_at__isnull=status == 'pending')
        return queryset


@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ('project', 'reporter', 'created_at', 'is_resolved')
    list_select_related = ('project', 'reporter')
    list_filter = (ReportStatusFilter, 'created_at')
    search_fields = ('project__name', 'reporter__username', 'reason')
    readonly_fields = (
        'project', 'reporter', 'reason', 'created_at', 'resolved_at',
        'resolved_by',
    )
    ordering = ('-created_at',)
    actions = ('resolve_reports',)

    def has_add_permission(self, request):
        return False

    @admin.display(boolean=True, description='Рассмотрена')
    def is_resolved(self, obj):
        return obj.resolved_at is not None

    @admin.action(
        permissions=['change'],
        description='Отметить выбранные жалобы как рассмотренные',
    )
    def resolve_reports(self, request, queryset):
        count = queryset.resolve(request.user)
        self.message_user(request, f'Рассмотрено жалоб: {count}.')
