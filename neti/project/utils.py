__all__ = ()


def has_pdf_signature(file):
    signature = file.read(5)
    file.seek(0)
    return signature == b'%PDF-'


def save_file_path_document(instance, filename):
    return f'user_{instance.user.id}/{instance.id}/document/{filename}'


def save_file_path_image(instance, filename):
    return (
        f'user_{instance.project.user.id}'
        f'/{instance.project.id}/images/{filename}'
    )
