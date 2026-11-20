__all__ = ()

from django import forms
from django.db import transaction
from PIL import Image as PillowImage

from project.models import Image, MainImage, Project, ProjectReport

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_GALLERY_IMAGES = 10


class DocumentField(forms.FileField):
    def to_python(self, data):
        upload = super().to_python(data)
        if upload is None:
            return None
        if upload.size > MAX_DOCUMENT_SIZE:
            raise forms.ValidationError('Документ не должен превышать 10 МБ.')
        header = upload.read(5)
        upload.seek(0)
        if not upload.name.lower().endswith('.pdf') or header != b'%PDF-':
            raise forms.ValidationError('Загрузите документ в формате PDF.')
        return upload


class ProjectImageField(forms.ImageField):
    def to_python(self, data):
        if data and data.size > MAX_IMAGE_SIZE:
            raise forms.ValidationError(
                'Изображение не должно превышать 5 МБ.',
            )
        upload = super().to_python(data)
        if upload is None:
            return None
        if upload.image.format not in {'JPEG', 'PNG', 'WEBP'}:
            raise forms.ValidationError('Допустимы JPEG, PNG и WebP.')
        if upload.image.width * upload.image.height > MAX_IMAGE_PIXELS:
            raise forms.ValidationError(
                'Изображение не должно превышать 16 мегапикселей.',
            )
        try:
            with PillowImage.open(upload) as image:
                image.load()
        except (OSError, ValueError) as error:
            raise forms.ValidationError(
                'Файл изображения повреждён.',
            ) from error
        upload.seek(0)
        return upload


class GalleryInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class GalleryField(ProjectImageField):
    widget = GalleryInput

    def clean(self, data, initial=None):
        uploads = data or []
        if len(uploads) > MAX_GALLERY_IMAGES:
            raise forms.ValidationError(
                'В галерее может быть не более 10 изображений.',
            )
        clean_image = super().clean
        return [clean_image(upload, initial) for upload in uploads]


class ProjectForm(forms.ModelForm):
    document = DocumentField(
        label='Документ',
        help_text='PDF до 10 МБ.',
        widget=forms.FileInput(attrs={'accept': 'application/pdf'}),
    )
    main_image = ProjectImageField(
        label='Главное изображение',
        required=False,
        help_text='JPEG, PNG или WebP до 5 МБ и 16 мегапикселей.',
    )
    gallery = GalleryField(
        label='Добавить изображения в галерею',
        required=False,
        help_text='До 10 изображений. Ограничения те же, что для главного.',
    )
    remove_images = forms.ModelMultipleChoiceField(
        queryset=Image.objects.none(),
        label='Удалить из галереи',
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Project
        fields = ('name', 'description', 'document', 'tags')
        labels = {'name': 'Название'}
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = self.fields['tags'].queryset.order_by(
            'name',
        )
        self.gallery_images = Image.objects.none()
        self.main_image = None
        if not self.instance._state.adding:
            self.gallery_images = self.instance.images.order_by('created_at')
            self.main_image = getattr(self.instance, 'main_image', None)
            if self.main_image:
                self.initial['main_image'] = self.main_image.main_image
        self.fields['remove_images'].queryset = self.gallery_images
        self.fields['remove_images'].label_from_instance = self.image_label
        if not self.gallery_images.exists():
            self.fields['remove_images'].widget = forms.MultipleHiddenInput()

    @staticmethod
    def image_label(image):
        if image.image:
            return image.image.name.rsplit('/', 1)[-1]
        return 'Без файла'

    def clean(self):
        cleaned_data = super().clean()
        added = cleaned_data.get('gallery')
        removed = cleaned_data.get('remove_images')
        if added and removed is not None:
            total = self.gallery_images.count() - len(removed) + len(added)
            if total > MAX_GALLERY_IMAGES:
                self.add_error(
                    'gallery',
                    'В галерее может быть не более 10 изображений.',
                )
        return cleaned_data

    def save_project(self):
        project = self.save(commit=False)
        new_files = []
        try:
            with transaction.atomic():
                if 'document' in self.changed_data:
                    self.save_upload(project.document, new_files)
                project.save()
                self.save_m2m()

                if 'main_image' in self.changed_data:
                    upload = self.cleaned_data['main_image']
                    if upload:
                        main = self.main_image or MainImage(project=project)
                        main.main_image = upload
                        self.save_upload(main.main_image, new_files)
                        main.save()
                    elif self.main_image:
                        self.main_image.delete()

                self.cleaned_data['remove_images'].delete()
                for upload in self.cleaned_data['gallery']:
                    image = Image(project=project, image=upload)
                    self.save_upload(image.image, new_files)
                    image.save()
        except Exception:
            for storage, name in new_files:
                storage.delete(name)
            raise
        return project

    @staticmethod
    def save_upload(field, new_files):
        field.save(field.name, field.file, save=False)
        new_files.append((field.storage, field.name))


class RatingForm(forms.Form):
    value = forms.IntegerField(label='Ваша оценка', min_value=1, max_value=10)


class ProjectSearchForm(forms.Form):
    q = forms.CharField(
        label='Поиск по названию',
        max_length=Project._meta.get_field('name').max_length,
        required=False,
        widget=forms.TextInput(
            attrs={'type': 'search', 'class': 'form-control'},
        ),
    )


class ProjectReportForm(forms.ModelForm):
    class Meta:
        model = ProjectReport
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'},
            ),
        }
