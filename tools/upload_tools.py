ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx'}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_upload(file, allowed_extensions=ALLOWED_EXTENSIONS, max_size_bytes=MAX_SIZE_BYTES):
    if not file or file.filename == '':
        return False, "Aucun fichier sélectionné"

    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return False, f"Extension non autorisée. Extensions acceptées: {', '.join(sorted(allowed_extensions))}"

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > max_size_bytes:
        return False, f"Fichier trop volumineux (max {max_size_bytes // (1024 * 1024)} Mo)"

    return True, None
