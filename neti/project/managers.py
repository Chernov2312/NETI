__all__ = ()
from django.apps import apps
from django.db import models
from django.db.models import Avg, OuterRef, Prefetch, Subquery
from django.utils import timezone


class ProjectManager(models.Manager):

    def _base_queryset(self, include_gallery=False):
        tag = apps.get_model('project', 'Tag')
        image = apps.get_model('project', 'Image')

        rating = apps.get_model('project', 'Rating')
        averages = (
            rating.objects.filter(project_id=OuterRef('pk'))
            .order_by()
            .values('project_id')
            .annotate(average=Avg('value'))
            .values('average')
        )
        queryset = (
            self.get_queryset()
            .select_related('main_image', 'user')
            .annotate(average_rating=Subquery(averages))
        )

        prefetch_list = [
            Prefetch('tags', queryset=tag.objects.only('name', 'slug')),
        ]
        project_fields = [
            'name',
            'description',
            'document',
            'main_image__main_image',
            'updated_at',
            'user__id',
            'user__username',
        ]

        if include_gallery:
            prefetch_list.append(
                Prefetch(
                    'images',
                    queryset=image.objects.only('image', 'project_id')
                    .order_by('created_at'),
                ),
            )

        return queryset.prefetch_related(*prefetch_list).only(*project_fields)

    def get_projects_main(self):
        return self._base_queryset(include_gallery=False).order_by(
            '-updated_at', '-id',
        )

    def get_project_info(self, id):
        return self._base_queryset(include_gallery=True).filter(id=id).first()


class ProjectReportQuerySet(models.QuerySet):
    def resolve(self, user):
        return self.filter(resolved_at__isnull=True).update(
            resolved_at=timezone.now(),
            resolved_by=user,
        )
