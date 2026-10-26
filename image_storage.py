"""Bounded image decoding and safe cleanup of generated upload paths."""
from io import BytesIO
import logging
from pathlib import Path
import warnings

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
import config

logger = logging.getLogger(__name__)
FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def verified_image(file):
    if not file.filename or not file.filename.strip():
        raise HTTPException(400, "An image filename is required")
    data = file.file.read(config.MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(400, "Image file is empty")
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image exceeds the upload size limit")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                image_format = image.format
                if image_format not in FORMATS:
                    raise HTTPException(415, "Only JPEG, PNG, and WEBP images are supported")
                if image.width * image.height > config.MAX_IMAGE_PIXELS:
                    raise HTTPException(413, "Image exceeds the pixel limit")
                if getattr(image, "n_frames", 1) != 1:
                    raise HTTPException(400, "Animated images are not supported")
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()
                # Re-encode pixels, dropping metadata and trailing payloads.
                clean = Image.new(image.mode, image.size)
                clean.paste(image)
                if image.mode == "P":
                    clean = image.convert("RGBA")
                output = BytesIO()
                clean.save(output, format=image_format)
                sanitized = output.getvalue()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(413, "Image exceeds the pixel limit") from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, EOFError):
        raise HTTPException(400, "Invalid or malformed image") from None
    if len(sanitized) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Processed image exceeds the upload size limit")
    return sanitized, FORMATS[image_format]


def cleanup_image(image_url, upload_dir):
    if not image_url:
        return
    if not image_url.startswith("/uploads/"):
        logger.warning("Skipped unsafe stored image path")
        return
    name = image_url.removeprefix("/uploads/")
    if not name or "/" in name or "\\" in name or Path(name).name != name:
        logger.warning("Skipped unsafe stored image path")
        return
    try:
        root = upload_dir.resolve()
        target = upload_dir / name
        if target.is_symlink() or target.resolve().parent != root:
            logger.warning("Skipped unsafe stored image path")
            return
        target.unlink(missing_ok=True)
    except OSError as error:
        # Cleanup failure cannot undo an already committed database operation.
        logger.error("Image cleanup failed (%s); storage maintenance required", type(error).__name__)
