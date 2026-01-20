"""Profile picture service for handling image uploads and storage."""
import os
import logging
from io import BytesIO
from PIL import Image
from flask import current_app
from app import db
from app.models import Member

# Register HEIF/HEIC support with Pillow
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed, HEIC/HEIF won't be supported

logger = logging.getLogger(__name__)

# Image processing constants
TARGET_SIZE = (400, 400)
JPEG_QUALITY = 85
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif'}


class ProfilePictureService:
    """Service for managing member profile pictures."""

    @staticmethod
    def get_upload_folder():
        """Get the upload folder path, creating it if necessary."""
        folder = current_app.config.get('PROFILE_PICTURE_UPLOAD_FOLDER')
        if not folder:
            # Fallback to instance/uploads/profile_pictures
            folder = os.path.join(current_app.instance_path, 'uploads', 'profile_pictures')

        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            logger.info(f"Created profile picture upload folder: {folder}")

        return folder

    @staticmethod
    def get_picture_path(member_id):
        """
        Get the file path for a member's profile picture.

        Args:
            member_id: ID of the member

        Returns:
            str: Full path to the profile picture file, or None if not found
        """
        folder = ProfilePictureService.get_upload_folder()
        path = os.path.join(folder, f"{member_id}.jpg")

        if os.path.exists(path):
            return path
        return None

    @staticmethod
    def allowed_file(filename):
        """Check if the file extension is allowed."""
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS

    @staticmethod
    def save_profile_picture(member_id, file):
        """
        Save a profile picture for a member.

        Processes the image: validates, resizes to 400x400, converts to JPEG.

        Args:
            member_id: ID of the member
            file: FileStorage object from request.files

        Returns:
            tuple: (success: bool, error_message: str | None)
        """
        try:
            # Validate member exists
            member = Member.query.get(member_id)
            if not member:
                return False, "Mitglied nicht gefunden"

            # Validate file
            if not file or not file.filename:
                return False, "Keine Datei ausgewählt"

            if not ProfilePictureService.allowed_file(file.filename):
                return False, "Ungültiges Dateiformat. Erlaubt: PNG, JPG, GIF, WebP"

            # Check file size (read into memory to process anyway)
            max_size = current_app.config.get('PROFILE_PICTURE_MAX_SIZE', 5 * 1024 * 1024)
            file_content = file.read()
            if len(file_content) > max_size:
                return False, f"Datei zu groß. Maximum: {max_size // (1024 * 1024)} MB"

            # Process image with Pillow
            try:
                image = Image.open(BytesIO(file_content))
            except Exception as e:
                logger.error(f"Failed to open image: {e}")
                return False, "Ungültige Bilddatei"

            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize with center crop to square
            image = ProfilePictureService._resize_and_crop(image, TARGET_SIZE)

            # Save as JPEG
            folder = ProfilePictureService.get_upload_folder()
            output_path = os.path.join(folder, f"{member_id}.jpg")

            image.save(output_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)

            # Update member record
            member.has_profile_picture = True
            member.profile_picture_version += 1
            db.session.commit()

            logger.info(f"Profile picture saved for member {member_id}, version {member.profile_picture_version}")

            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save profile picture for member {member_id}: {e}")
            return False, f"Fehler beim Speichern des Profilbilds: {str(e)}"

    @staticmethod
    def _resize_and_crop(image, target_size):
        """
        Resize image to target size with center crop.

        Args:
            image: PIL Image object
            target_size: Tuple of (width, height)

        Returns:
            PIL Image object resized and cropped
        """
        # Calculate aspect ratios
        img_ratio = image.width / image.height
        target_ratio = target_size[0] / target_size[1]

        if img_ratio > target_ratio:
            # Image is wider - crop width
            new_height = image.height
            new_width = int(new_height * target_ratio)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, new_height))
        elif img_ratio < target_ratio:
            # Image is taller - crop height
            new_width = image.width
            new_height = int(new_width / target_ratio)
            top = (image.height - new_height) // 2
            image = image.crop((0, top, new_width, top + new_height))

        # Resize to target
        image = image.resize(target_size, Image.Resampling.LANCZOS)

        return image

    @staticmethod
    def delete_profile_picture(member_id):
        """
        Delete a member's profile picture.

        Args:
            member_id: ID of the member

        Returns:
            tuple: (success: bool, error_message: str | None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return False, "Mitglied nicht gefunden"

            if not member.has_profile_picture:
                return False, "Kein Profilbild vorhanden"

            # Delete file
            path = ProfilePictureService.get_picture_path(member_id)
            if path and os.path.exists(path):
                os.remove(path)
                logger.info(f"Deleted profile picture file for member {member_id}")

            # Update member record
            member.has_profile_picture = False
            # Note: We don't reset version - this ensures cached images are invalidated
            member.profile_picture_version += 1
            db.session.commit()

            logger.info(f"Profile picture deleted for member {member_id}")

            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete profile picture for member {member_id}: {e}")
            return False, f"Fehler beim Löschen des Profilbilds: {str(e)}"

    @staticmethod
    def get_profile_picture_data(member_id):
        """
        Get profile picture data for a member.

        Args:
            member_id: ID of the member

        Returns:
            tuple: (bytes data or None, error_message: str | None)
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return None, "Mitglied nicht gefunden"

            if not member.has_profile_picture:
                return None, "Kein Profilbild vorhanden"

            path = ProfilePictureService.get_picture_path(member_id)
            if not path:
                # File missing but flag set - fix inconsistency
                member.has_profile_picture = False
                db.session.commit()
                return None, "Profilbild nicht gefunden"

            with open(path, 'rb') as f:
                return f.read(), None

        except Exception as e:
            logger.error(f"Failed to get profile picture for member {member_id}: {e}")
            return None, f"Fehler beim Laden des Profilbilds: {str(e)}"
