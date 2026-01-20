"""Tests for profile picture service."""
import pytest
import os
import io
from PIL import Image
from app import db
from app.models import Member
from app.services.profile_picture_service import ProfilePictureService, ALLOWED_EXTENSIONS


class MockFileStorage:
    """Mock file storage for testing."""

    def __init__(self, filename, content, content_type='image/jpeg'):
        self.filename = filename
        self._content = content
        self.content_type = content_type
        self._position = 0

    def read(self):
        return self._content

    def seek(self, position):
        self._position = position


def create_test_image(width=100, height=100, format='JPEG'):
    """Create a test image in memory."""
    img = Image.new('RGB', (width, height), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


class TestAllowedFile:
    """Tests for file extension validation."""

    def test_allowed_extensions(self):
        """Should accept allowed extensions."""
        for ext in ALLOWED_EXTENSIONS:
            assert ProfilePictureService.allowed_file(f'image.{ext}') is True
            assert ProfilePictureService.allowed_file(f'image.{ext.upper()}') is True

    def test_disallowed_extensions(self):
        """Should reject disallowed extensions."""
        assert ProfilePictureService.allowed_file('image.exe') is False
        assert ProfilePictureService.allowed_file('image.txt') is False
        assert ProfilePictureService.allowed_file('image.pdf') is False

    def test_no_extension(self):
        """Should reject files without extension."""
        assert ProfilePictureService.allowed_file('image') is False

    def test_empty_filename(self):
        """Should reject empty filename."""
        assert ProfilePictureService.allowed_file('') is False
        assert ProfilePictureService.allowed_file(None) is False


class TestSaveProfilePicture:
    """Tests for saving profile pictures."""

    def test_save_member_not_found(self, app):
        """Should fail for non-existent member."""
        with app.app_context():
            image_data = create_test_image()
            mock_file = MockFileStorage('test.jpg', image_data)

            success, error = ProfilePictureService.save_profile_picture(
                'non-existent-id',
                mock_file
            )

            assert success is False
            assert 'nicht gefunden' in error

    def test_save_no_file(self, app):
        """Should fail when no file provided."""
        with app.app_context():
            member = Member(
                firstname='NoFile',
                lastname='Test',
                email='nofile@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            success, error = ProfilePictureService.save_profile_picture(member.id, None)

            assert success is False
            assert 'Keine Datei' in error

    def test_save_invalid_extension(self, app):
        """Should fail for invalid file extension."""
        with app.app_context():
            member = Member(
                firstname='Invalid',
                lastname='Ext',
                email='invalid_ext@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            mock_file = MockFileStorage('test.exe', b'fake content')
            success, error = ProfilePictureService.save_profile_picture(member.id, mock_file)

            assert success is False
            assert 'Ungültiges Dateiformat' in error

    def test_save_valid_image(self, app):
        """Should save valid image successfully."""
        with app.app_context():
            member = Member(
                firstname='Valid',
                lastname='Image',
                email='valid_image@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
            member_id = member.id

            image_data = create_test_image(200, 200)
            mock_file = MockFileStorage('test.jpg', image_data)

            success, error = ProfilePictureService.save_profile_picture(member_id, mock_file)

            assert success is True
            assert error is None

            # Verify member record updated
            refreshed = Member.query.get(member_id)
            assert refreshed.has_profile_picture is True
            assert refreshed.profile_picture_version >= 1

            # Clean up
            path = ProfilePictureService.get_picture_path(member_id)
            if path and os.path.exists(path):
                os.remove(path)

    def test_save_png_with_transparency(self, app):
        """Should handle PNG with transparency."""
        with app.app_context():
            member = Member(
                firstname='Png',
                lastname='Test',
                email='png_test@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
            member_id = member.id

            # Create PNG with alpha channel
            img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = buffer.getvalue()

            mock_file = MockFileStorage('test.png', image_data)
            success, error = ProfilePictureService.save_profile_picture(member_id, mock_file)

            assert success is True

            # Clean up
            path = ProfilePictureService.get_picture_path(member_id)
            if path and os.path.exists(path):
                os.remove(path)

    def test_save_non_square_image(self, app):
        """Should crop non-square images to square."""
        with app.app_context():
            member = Member(
                firstname='NonSquare',
                lastname='Test',
                email='nonsquare@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
            member_id = member.id

            # Create wide image
            image_data = create_test_image(400, 200)
            mock_file = MockFileStorage('test.jpg', image_data)

            success, error = ProfilePictureService.save_profile_picture(member_id, mock_file)

            assert success is True

            # Clean up
            path = ProfilePictureService.get_picture_path(member_id)
            if path and os.path.exists(path):
                os.remove(path)


class TestDeleteProfilePicture:
    """Tests for deleting profile pictures."""

    def test_delete_member_not_found(self, app):
        """Should fail for non-existent member."""
        with app.app_context():
            success, error = ProfilePictureService.delete_profile_picture('non-existent-id')

            assert success is False
            assert 'nicht gefunden' in error

    def test_delete_no_picture(self, app):
        """Should fail when no picture exists."""
        with app.app_context():
            member = Member(
                firstname='NoPicture',
                lastname='Delete',
                email='nopicture_delete@example.com',
                role='member',
                has_profile_picture=False
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            success, error = ProfilePictureService.delete_profile_picture(member.id)

            assert success is False
            assert 'Kein Profilbild' in error

    def test_delete_success(self, app):
        """Should delete profile picture successfully."""
        with app.app_context():
            member = Member(
                firstname='Delete',
                lastname='Test',
                email='delete_test@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
            member_id = member.id

            # First save a picture
            image_data = create_test_image()
            mock_file = MockFileStorage('test.jpg', image_data)
            ProfilePictureService.save_profile_picture(member_id, mock_file)

            # Now delete it
            success, error = ProfilePictureService.delete_profile_picture(member_id)

            assert success is True
            assert error is None

            refreshed = Member.query.get(member_id)
            assert refreshed.has_profile_picture is False


class TestGetProfilePictureData:
    """Tests for getting profile picture data."""

    def test_get_member_not_found(self, app):
        """Should fail for non-existent member."""
        with app.app_context():
            data, error = ProfilePictureService.get_profile_picture_data('non-existent-id')

            assert data is None
            assert 'nicht gefunden' in error

    def test_get_no_picture(self, app):
        """Should return None when no picture exists."""
        with app.app_context():
            member = Member(
                firstname='NoPicture',
                lastname='Get',
                email='nopicture_get@example.com',
                role='member',
                has_profile_picture=False
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            data, error = ProfilePictureService.get_profile_picture_data(member.id)

            assert data is None
            assert 'Kein Profilbild' in error

    def test_get_success(self, app):
        """Should return picture data successfully."""
        with app.app_context():
            member = Member(
                firstname='Get',
                lastname='Test',
                email='get_test@example.com',
                role='member'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
            member_id = member.id

            # First save a picture
            image_data = create_test_image()
            mock_file = MockFileStorage('test.jpg', image_data)
            ProfilePictureService.save_profile_picture(member_id, mock_file)

            # Now get it
            data, error = ProfilePictureService.get_profile_picture_data(member_id)

            assert data is not None
            assert error is None
            assert len(data) > 0

            # Clean up
            path = ProfilePictureService.get_picture_path(member_id)
            if path and os.path.exists(path):
                os.remove(path)


class TestResizeAndCrop:
    """Tests for image resizing and cropping."""

    def test_resize_wider_image(self, app):
        """Should crop and resize wider image."""
        with app.app_context():
            img = Image.new('RGB', (400, 200), color='blue')
            result = ProfilePictureService._resize_and_crop(img, (100, 100))

            assert result.size == (100, 100)

    def test_resize_taller_image(self, app):
        """Should crop and resize taller image."""
        with app.app_context():
            img = Image.new('RGB', (200, 400), color='green')
            result = ProfilePictureService._resize_and_crop(img, (100, 100))

            assert result.size == (100, 100)

    def test_resize_square_image(self, app):
        """Should resize square image without cropping."""
        with app.app_context():
            img = Image.new('RGB', (200, 200), color='red')
            result = ProfilePictureService._resize_and_crop(img, (100, 100))

            assert result.size == (100, 100)
