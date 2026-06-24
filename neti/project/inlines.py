__all__ = ()
from django.contrib import admin

from project.models import Image, MainImage


class ImageInline(admin.TabularInline):
    model = Image
    extra = 3
    fields = (Image.image.field.name, 'get_image_300x300')
    readonly_fields = ('get_image_300x300',)
    verbose_name = 'дополнительное изображение'


class MainImageInline(admin.TabularInline):
    model = MainImage
    extra = 1
    fields = (MainImage.main_image.field.name, 'get_image_300x300')
    readonly_fields = ('get_image_300x300',)
    verbose_name = 'главное изображение'
