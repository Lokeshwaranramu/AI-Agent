"""
Image modification tools using Pillow.
Supports: resize, crop, rotate, flip, brightness, contrast, format conversion,
          watermark, text overlay, thumbnail generation.
"""
import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from utils.logger import log


def resize_image(
    input_path: str,
    width: int,
    height: int,
    output_path: Optional[str] = None,
    maintain_aspect: bool = True,
) -> str:
    """
    Resize an image to specified dimensions.

    Args:
        input_path: Source image path
        width: Target width in pixels
        height: Target height in pixels
        output_path: Output path (auto-generated if None)
        maintain_aspect: If True, maintains aspect ratio using thumbnail method

    Returns:
        Path to the resized image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + f"_resized_{width}x{height}"))

    try:
        img = Image.open(input_path)
        if maintain_aspect:
            img.thumbnail((width, height), Image.LANCZOS)
        else:
            img = img.resize((width, height), Image.LANCZOS)

        os.makedirs(Path(output_path).parent, exist_ok=True)
        img.save(output_path)
        log.success(f"Image resized to {width}x{height}: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Image resize failed: {e}")
        raise


def convert_image_format(
    input_path: str,
    target_format: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Convert image to a different format.

    Args:
        input_path: Source image path
        target_format: Target format string e.g. 'PNG', 'JPEG', 'WEBP', 'BMP'
        output_path: Output path (auto-generated if None)

    Returns:
        Path to the converted image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    fmt = target_format.upper()
    extension_map = {
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "GIF": ".gif",
    }
    ext = extension_map.get(fmt, f".{fmt.lower()}")

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_suffix(ext))

    try:
        img = Image.open(input_path)
        if fmt in ("JPEG", "JPG") and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        os.makedirs(Path(output_path).parent, exist_ok=True)
        img.save(output_path, format=fmt)
        log.success(f"Image converted to {fmt}: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Image format conversion failed: {e}")
        raise


def add_watermark(
    input_path: str,
    watermark_text: str,
    output_path: Optional[str] = None,
    opacity: int = 128,
    position: str = "center",
) -> str:
    """
    Add a text watermark to an image.

    Args:
        input_path: Source image path
        watermark_text: Text to use as watermark
        output_path: Output path
        opacity: Watermark opacity 0-255 (128 = 50%)
        position: 'center', 'bottom-right', 'bottom-left', 'top-right', 'top-left'

    Returns:
        Path to the watermarked image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + "_watermarked"))

    try:
        img = Image.open(input_path).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype(
                r"C:\Windows\Fonts\Arial.ttf", 40
            )
        except (IOError, OSError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        w, h = img.size
        padding = 20
        position_map = {
            "center": ((w - text_w) // 2, (h - text_h) // 2),
            "bottom-right": (w - text_w - padding, h - text_h - padding),
            "bottom-left": (padding, h - text_h - padding),
            "top-right": (w - text_w - padding, padding),
            "top-left": (padding, padding),
        }
        pos = position_map.get(position, position_map["center"])

        draw.text(pos, watermark_text, fill=(255, 255, 255, opacity), font=font)
        watermarked = Image.alpha_composite(img, overlay).convert("RGB")

        os.makedirs(Path(output_path).parent, exist_ok=True)
        watermarked.save(output_path)
        log.success(f"Watermark added: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Watermark failed: {e}")
        raise


def adjust_image(
    input_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
    output_path: Optional[str] = None,
) -> str:
    """
    Adjust image brightness, contrast, saturation, and sharpness.
    Values: 1.0 = original, <1.0 = decrease, >1.0 = increase.

    Args:
        input_path: Source image path
        brightness: 0.0 (black) to 2.0+ (bright), 1.0 = original
        contrast: 0.0 (gray) to 2.0+ (high), 1.0 = original
        saturation: 0.0 (grayscale) to 2.0+, 1.0 = original
        sharpness: 0.0 (blur) to 2.0+ (sharp), 1.0 = original
        output_path: Output path

    Returns:
        Path to the adjusted image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + "_adjusted"))

    try:
        img = Image.open(input_path)

        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)

        os.makedirs(Path(output_path).parent, exist_ok=True)
        img.save(output_path)
        log.success(f"Image adjusted and saved: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Image adjustment failed: {e}")
        raise


def crop_image(
    input_path: str,
    left: int,
    upper: int,
    right: int,
    lower: int,
    output_path: Optional[str] = None,
) -> str:
    """
    Crop an image to a bounding box (left, upper, right, lower) in pixels.

    Returns:
        Path to the cropped image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + "_cropped"))

    try:
        img = Image.open(input_path)
        cropped = img.crop((left, upper, right, lower))
        os.makedirs(Path(output_path).parent, exist_ok=True)
        cropped.save(output_path)
        log.success(f"Image cropped: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Image crop failed: {e}")
        raise
