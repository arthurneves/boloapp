import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

class ImageService:
    UPLOAD_FOLDER = 'static/uploads/profile_photos'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @classmethod
    def allowed_file(cls, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS

    @classmethod
    def save_profile_photo(cls, file, custom_name=None):
        if not file or file.filename == '':
            return None

        if not cls.allowed_file(file.filename):
            raise ValueError("Arquivo de imagem inválido. Use PNG, JPG ou GIF.")

        # Ensure upload directory exists
        upload_path = os.path.join(current_app.root_path, cls.UPLOAD_FOLDER)
        os.makedirs(upload_path, exist_ok=True)

        file_extension = file.filename.rsplit('.', 1)[1].lower()

        if custom_name:
            unique_filename = f"{custom_name}.{file_extension}"
        else:
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
        filepath = os.path.join(upload_path, unique_filename)

        # Save original image
        file.save(filepath)

        return {
            'original': unique_filename
        }

    @classmethod
    def delete_profile_photo(cls, photo_path):
        """
        Delete existing profile photo
        """
        if not photo_path:
            return

        # Construct full paths
        base_path = current_app.root_path
        full_photo_path = os.path.join(base_path, ImageService.UPLOAD_FOLDER, photo_path)

        # Remove files if they exist
        try:
            if os.path.exists(full_photo_path):
                os.remove(full_photo_path)
        except Exception as e:
            print(f"Erro ao excluir foto: {e}")
