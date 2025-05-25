import tempfile

from fastapi import UploadFile


def save_upload_file(file: UploadFile, suffix=".wav") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        file_content = file.file.read()
        temp_file.write(file_content)
        return temp_file.name
