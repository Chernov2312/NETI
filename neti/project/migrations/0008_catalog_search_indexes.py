from django.db import migrations, models


def add_name_search_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
        schema_editor.execute(
            'CREATE INDEX project_name_trgm_idx ON project_project '
            'USING gin (UPPER(name::text) gin_trgm_ops)',
        )


def remove_name_search_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('DROP INDEX project_name_trgm_idx')


class Migration(migrations.Migration):
    dependencies = [
        ('project', '0007_localize_catalog_admin'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='project',
            index=models.Index(
                fields=['-updated_at', '-id'],
                name='project_updated_id_idx',
            ),
        ),
        migrations.RunPython(add_name_search_index, remove_name_search_index),
    ]
