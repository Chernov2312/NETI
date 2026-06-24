__all__ = ()
from django.contrib import admin

from project.inlines import ImageInline, MainImageInline
from project.models import Image, MainImage, Project, Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'value')
    list_filter = ('value', 'project')
    search_fields = ('project__name', 'user__username')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = (Image.image.field.name, 'get_image_300x300')
    list_filter = ('project',)


@admin.register(MainImage)
class MainImagegAdmin(admin.ModelAdmin):
    list_display = (MainImage.main_image.field.name, 'get_image_300x300')
    list_filter = ('project',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = (ImageInline, MainImageInline)
    filter_horizontal = (Project.tags.field.name,)
    prepopulated_fields = {'slug': ('name',)}
    @admin.display(description='Главное изображение')
    def main_image_tmb(self, obj):
        if obj.main_image:
            return obj.main_image.image_tmb()

        return 'Нет изображения'

    @admin.display(description='Другие изображения')
    def image_tmb(self, obj):
        if obj.image:
            return obj.image.image_tmb()

        return 'Нет изображения'
