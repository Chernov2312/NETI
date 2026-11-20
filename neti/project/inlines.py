__all__ = ()
from django.contrib import admin
from django.db import models

from project.forms import ProjectImageField
from project.models import Image, MainImage


class ProjectImageInline(admin.TabularInline):
    readonly_fields = ('get_image_tmb',)
    formfield_overrides = {
        models.ImageField: {'form_class': ProjectImageField},
    }


class ImageInline(ProjectImageInline):
    model = Image
    extra = 3
    fields = ('image', 'get_image_tmb')


class MainImageInline(ProjectImageInline):
    model = MainImage
    extra = 1
    fields = ('main_image', 'get_image_tmb')
