from django.apps import apps
from django.db import models
from django.db.models import Avg, Prefetch

__all__ = ['ProjectManager']


class ProjectManager(models.Manager):

    def _base_queryset(self, include_gallery=False):
        tag = apps.get_model('project', 'Tag')
        image = apps.get_model('project', 'Image')

        queryset = (
            self.get_queryset()
            .select_related('main_image')
            .annotate(average_rating=Avg('ratings__value'))
        )

        prefetch_list = [Prefetch('tags', queryset=tag.objects.only('name'))]
        project_fields = [
            'name',
            'description',
            'main_image__main_image',
            'updated_at',
        ]

        if include_gallery:
            prefetch_list.append(
                Prefetch('images', queryset=image.objects.only('image')),
            )

        return queryset.prefetch_related(*prefetch_list).only(*project_fields)

    def get_projects_main(self):
        return self._base_queryset(include_gallery=False).order_by(
            '-updated_at',
        )

    def get_project_info(self):
        return self._base_queryset(include_gallery=True).order_by(
            '-updated_at',
        )
