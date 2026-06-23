__all__ = ()


def save_file_path_document(instance, filename):
    return f'user_{instance.user.id}/{instance.project.id}/document/{filename}'


def save_file_path_image(instance, filename):
    return f'user_{instance.project.user.id}/{instance.project.id}/images/{filename}'
