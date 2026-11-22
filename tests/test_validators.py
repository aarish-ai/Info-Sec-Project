import io
import pytest
from werkzeug.datastructures import FileStorage
from app.core.validators import validate_upload

def create_file_storage(data: bytes, filename: str) -> FileStorage:
    """Helper to create a FileStorage object wrapping an in-memory byte stream."""
    stream = io.BytesIO(data)
    return FileStorage(stream=stream, filename=filename)

def test_validate_genuine_jpeg():
    # Valid JPEG header: \xFF\xD8\xFF\xE0...
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00' + b'A' * 50
    file_storage = create_file_storage(jpeg_data, "photo.jpg")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is True
    assert err == ""
    assert mime == "image/jpeg"
    assert file_storage.tell() == 0

def test_validate_genuine_jpeg_with_jpeg_extension():
    jpeg_data = b'\xff\xd8\xff\xe1\x00\x18Exif\x00\x00' + b'B' * 50
    file_storage = create_file_storage(jpeg_data, "camera_shot.jpeg")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is True
    assert err == ""
    assert mime == "image/jpeg"
    assert file_storage.tell() == 0

def test_validate_genuine_png():
    # Valid PNG header: \x89PNG\r\n\x1a\n...
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'P' * 50
    file_storage = create_file_storage(png_data, "graphic.png")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is True
    assert err == ""
    assert mime == "image/png"
    assert file_storage.tell() == 0

def test_validate_genuine_mp4():
    # Valid MP4 header: 4 bytes length + 'ftyp' + brand
    mp4_data = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42' + b'V' * 50
    file_storage = create_file_storage(mp4_data, "video.mp4")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is True
    assert err == ""
    assert mime == "video/mp4"
    assert file_storage.tell() == 0

def test_validate_genuine_mov():
    # Valid MOV header with ftypqt
    mov_data = b'\x00\x00\x00\x14ftypqt  \x00\x00\x00\x00' + b'M' * 50
    file_storage = create_file_storage(mov_data, "clip.mov")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is True
    assert err == ""
    assert mime == "video/quicktime"
    assert file_storage.tell() == 0

def test_validate_spoofed_extension_text_renamed_to_png():
    # Plain text file disguised with .png extension
    fake_png = b'This is clearly a plain text file, not a PNG image!'
    file_storage = create_file_storage(fake_png, "invoice.png")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is False
    assert "magic bytes" in err.lower() or "signature" in err.lower()
    assert mime == ""
    assert file_storage.tell() == 0

def test_validate_mismatched_extension_jpeg_named_png():
    # Real JPEG magic bytes, but named .png
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'X' * 50
    file_storage = create_file_storage(jpeg_data, "deceptive.png")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is False
    assert "extension" in err.lower()
    assert file_storage.tell() == 0

def test_validate_oversized_file():
    # File larger than custom max_size
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'P' * 200
    file_storage = create_file_storage(png_data, "big_graphic.png")
    
    is_valid, err, mime = validate_upload(file_storage, max_size=100)
    assert is_valid is False
    assert "exceeds" in err.lower()
    assert mime == ""
    assert file_storage.tell() == 0

def test_validate_empty_file():
    empty_data = b''
    file_storage = create_file_storage(empty_data, "empty.png")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is False
    assert "empty" in err.lower() or "0 bytes" in err.lower()
    assert mime == ""

def test_validate_unsupported_extension():
    pdf_data = b'%PDF-1.4\n%test'
    file_storage = create_file_storage(pdf_data, "document.pdf")
    
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is False
    assert "unsupported" in err.lower() or "extension" in err.lower()
    assert mime == ""

def test_validate_missing_or_invalid_file_storage():
    is_valid, err, mime = validate_upload(None)
    assert is_valid is False
    assert "no file" in err.lower()

    file_storage = create_file_storage(b'data', "")
    is_valid, err, mime = validate_upload(file_storage)
    assert is_valid is False
