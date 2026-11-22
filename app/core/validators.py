import io
import os
from typing import Tuple
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'mov'}

EXTENSION_MIME_MAP = {
    'jpg': {'image/jpeg'},
    'jpeg': {'image/jpeg'},
    'png': {'image/png'},
    'mp4': {'video/mp4'},
    'mov': {'video/quicktime', 'video/mp4'},
}

def detect_mime_type_from_header(header: bytes) -> str:
    """
    Detects MIME type from the initial binary header magic bytes.
    Returns the MIME type string, or empty string if unrecognized.
    """
    if len(header) < 3:
        return ""

    # JPEG starts with \xFF\xD8\xFF
    if header.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"

    # PNG starts with \x89PNG\r\n\x1a\n
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"

    # MOV can contain 'ftypqt', 'moov', 'wide', or 'free' within first 12 bytes
    first_12 = header[:12]
    first_16 = header[:16]
    if (
        b'ftypqt' in first_16
        or b'moov' in first_12
        or b'wide' in first_12
        or b'free' in first_12
    ):
        return "video/quicktime"

    # MP4 contains 'ftyp' within first 12 bytes
    if b'ftyp' in first_12:
        return "video/mp4"

    return ""

def validate_upload(
    file_storage,
    max_size: int = 50 * 1024 * 1024
) -> Tuple[bool, str, str]:
    """
    Validates an incoming uploaded file:
    1. Checks file presence and filename safety via secure_filename.
    2. Validates file extension against allowed formats.
    3. Sniffs initial header magic bytes to verify true file format.
    4. Validates that the file extension aligns with detected MIME type.
    5. Enforces maximum file size limit (default 50MB) and non-empty payload.
    6. Always resets the stream position to 0.

    Returns:
        (is_valid: bool, error_message: str, detected_mime_type: str)
    """
    if file_storage is None:
        return False, "No file provided", ""

    raw_filename = getattr(file_storage, 'filename', '') or ''
    if not raw_filename.strip():
        return False, "No file provided or empty filename", ""

    safe_name = secure_filename(raw_filename)
    if not safe_name:
        return False, "Invalid or unsafe filename", ""

    # Extension check
    if '.' not in safe_name:
        return False, "File must have a valid extension", ""

    ext = safe_name.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}", ""

    # Check file size early
    try:
        file_storage.seek(0, os.SEEK_END)
        file_size = file_storage.tell()
        file_storage.seek(0)
    except Exception as e:
        return False, f"Failed to determine file size: {str(e)}", ""

    if file_size == 0:
        return False, "File is empty (0 bytes)", ""

    if file_size > max_size:
        return False, f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)", ""

    # Read header magic bytes
    try:
        file_storage.seek(0)
        header = file_storage.read(64)
    except Exception as e:
        return False, f"Failed to read file stream: {str(e)}", ""

    detected_mime = detect_mime_type_from_header(header)
    if not detected_mime:
        try:
            file_storage.seek(0)
        except Exception:
            pass
        return False, "File signature (magic bytes) does not match supported formats", ""

    # Validate extension aligns with detected MIME type
    allowed_mimes_for_ext = EXTENSION_MIME_MAP.get(ext, set())
    if detected_mime not in allowed_mimes_for_ext:
        try:
            file_storage.seek(0)
        except Exception:
            pass
        return False, f"File extension .{ext} does not match actual content type {detected_mime}", ""

    try:
        file_storage.seek(0)
    except Exception:
        pass

    return True, "", detected_mime
