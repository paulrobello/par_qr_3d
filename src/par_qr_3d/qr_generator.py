"""QR code generation module with support for different data types."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import cast

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

from .logging_config import get_logger

logger = get_logger(__name__)


class ErrorCorrectionLevel(str, Enum):
    """QR code error correction levels.

    Defines the amount of error correction data included in the QR code.
    Higher levels allow more damage to the code while remaining scannable,
    but increase the QR code size.

    Attributes:
        LOW: ~7% error correction capability.
        MEDIUM: ~15% error correction capability.
        QUARTILE: ~25% error correction capability.
        HIGH: ~30% error correction capability.
    """

    LOW = "L"
    MEDIUM = "M"
    QUARTILE = "Q"
    HIGH = "H"


class QRType(str, Enum):
    """Supported QR code data types.

    Defines the different types of data that can be encoded in QR codes.
    Each type has specific formatting rules for optimal scanning by
    QR code readers.

    Attributes:
        TEXT: Plain text data.
        URL: Web URLs (http/https will be added if missing).
        EMAIL: Email addresses with optional subject and body.
        PHONE: Phone numbers (tel: format).
        SMS: SMS messages with phone number and optional message.
        WIFI: WiFi network credentials.
        CONTACT: vCard format contact information.
    """

    TEXT = "text"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WIFI = "wifi"
    CONTACT = "contact"


# Mapping from our error correction enum to qrcode library constants
ERROR_CORRECTION_MAP = {
    ErrorCorrectionLevel.LOW: ERROR_CORRECT_L,
    ErrorCorrectionLevel.MEDIUM: ERROR_CORRECT_M,
    ErrorCorrectionLevel.QUARTILE: ERROR_CORRECT_Q,
    ErrorCorrectionLevel.HIGH: ERROR_CORRECT_H,
}


def format_qr_data(data: str, qr_type: QRType, **kwargs: str) -> str:
    """Format data based on QR code type.

    Args:
        data: The main data content
        qr_type: The type of QR code to generate
        **kwargs: Additional parameters for specific QR types

    Returns:
        Formatted data string for QR code
    """
    if qr_type == QRType.TEXT:
        return data

    elif qr_type == QRType.URL:
        # Ensure URL has protocol
        if not data.startswith(("http://", "https://")):
            data = f"https://{data}"
        return data

    elif qr_type == QRType.EMAIL:
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        result = f"mailto:{data}"
        params = []
        if subject:
            params.append(f"subject={subject}")
        if body:
            params.append(f"body={body}")
        if params:
            result += "?" + "&".join(params)
        return result

    elif qr_type == QRType.PHONE:
        # Remove non-numeric characters except + for international
        cleaned = "".join(c for c in data if c.isdigit() or c == "+")
        return f"tel:{cleaned}"

    elif qr_type == QRType.SMS:
        message = kwargs.get("message", "")
        if message:
            return f"smsto:{data}:{message}"
        return f"smsto:{data}"

    elif qr_type == QRType.WIFI:
        ssid = data
        password = kwargs.get("password", "")
        security = kwargs.get("security", "WPA")  # WPA, WEP, or nopass
        hidden = kwargs.get("hidden", "false")
        return f"WIFI:T:{security};S:{ssid};P:{password};H:{hidden};;"

    elif qr_type == QRType.CONTACT:
        # Simple vCard format
        name = data
        phone = kwargs.get("phone", "")
        email = kwargs.get("email", "")
        org = kwargs.get("org", "")

        vcard = "BEGIN:VCARD\nVERSION:3.0\n"
        vcard += f"FN:{name}\n"
        if phone:
            vcard += f"TEL:{phone}\n"
        if email:
            vcard += f"EMAIL:{email}\n"
        if org:
            vcard += f"ORG:{org}\n"
        vcard += "END:VCARD"
        return vcard

    else:
        logger.warning(f"Unknown QR type: {qr_type}, treating as text")
        return data


def generate_qr_code(
    data: str,
    qr_type: QRType = QRType.TEXT,
    size: int = 200,
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.LOW,
    border: int = 4,
    **format_kwargs: str,
) -> Image.Image:
    """Generate a QR code image.

    Args:
        data: The data to encode
        qr_type: The type of QR code to generate
        size: The size of the QR code image in pixels (width and height)
        error_correction: Error correction level
        border: Border size in modules
        **format_kwargs: Additional parameters for specific QR types

    Returns:
        PIL Image object containing the QR code
    """
    # Format data based on type
    formatted_data = format_qr_data(data, qr_type, **format_kwargs)
    logger.debug(f"Generating QR code for: {formatted_data[:50]}...")

    # Create QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version
        error_correction=ERROR_CORRECTION_MAP[error_correction],
        box_size=10,  # Will be resized later
        border=border,
    )

    qr.add_data(formatted_data)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Cast to PIL Image for type checker
    pil_img = cast(Image.Image, img)

    # Resize to requested size
    pil_img = pil_img.resize((size, size), Image.Resampling.NEAREST)

    logger.info(f"Generated QR code: {size}x{size}px, error correction: {error_correction.value}")
    return pil_img


def crop_qr_border(
    image: Image.Image,
    crop_pixels: int = 0,
) -> Image.Image:
    """Crop white border from QR code image.

    Args:
        image: PIL Image of the QR code
        crop_pixels: Number of pixels to crop from each side

    Returns:
        Cropped PIL Image
    """
    if crop_pixels <= 0:
        return image

    width, height = image.size

    # Calculate crop box (left, top, right, bottom)
    crop_box = (crop_pixels, crop_pixels, width - crop_pixels, height - crop_pixels)

    # Ensure we don't crop too much
    if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
        logger.warning(f"Crop size {crop_pixels} is too large for image size {width}x{height}, skipping crop")
        return image

    cropped = image.crop(crop_box)
    logger.debug(f"Cropped QR code from {width}x{height} to {cropped.width}x{cropped.height}")

    return cropped


def add_label_to_qr(
    image: Image.Image,
    label: str,
    position: str = "top",
    margin: int = 2,
    threshold: int = 128,
) -> Image.Image:
    """Add a text label to a QR code image.

    Args:
        image: PIL Image of the QR code
        label: Text to add as label
        position: Position of the label ("top" or "bottom")
        margin: Margin in pixels between label and QR code
        threshold: Threshold value for binarization (0-255), pixels above this become white

    Returns:
        New PIL Image with label added
    """
    # Get image dimensions
    width, height = image.size

    # Load Roboto Black font for clear 3D printing
    font = None
    actual_font_size = 16  # Use 16px for better readability in 3D prints

    # Try to load Roboto Black font
    font_path = Path(__file__).parent / "fonts" / "Roboto-Black.ttf"
    try:
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), actual_font_size)
            logger.debug(f"Loaded Roboto Black font at size {actual_font_size}")
        else:
            logger.warning(f"Font file not found at {font_path}")
    except Exception as e:
        logger.warning(f"Could not load Roboto Black font: {e}")

    # Fall back to default font if needed
    if font is None:
        try:
            font = ImageFont.load_default()
            logger.debug("Using default font")
        except Exception:
            logger.error("Could not load any font")
            return image

    # Get actual text dimensions using the font
    draw_dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bbox = draw_dummy.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate new image dimensions
    new_height = int(height + text_height + margin * 3)  # Extra margin for better spacing

    # Create new image with white background
    if position == "top":
        new_image = Image.new("RGB", (width, new_height), "white")
        # Paste QR code below the label area
        new_image.paste(image, (0, int(text_height + margin * 2)))
        text_y = margin
    else:  # bottom
        new_image = Image.new("RGB", (width, new_height), "white")
        # Paste QR code at the top
        new_image.paste(image, (0, 0))
        text_y = int(height + margin)

    # Draw the label
    draw = ImageDraw.Draw(new_image)

    # Center the text horizontally
    text_x = (width - text_width) // 2
    text_x = max(0, text_x)  # Ensure non-negative

    # Draw text in black
    draw.text((text_x, text_y), label, fill="black", font=font)

    logger.info(f"Added label '{label}' at {position} position with Roboto Black font")

    # Convert to grayscale and apply threshold to remove antialiasing
    # This ensures pure black and white pixels for clean 3D printing
    gray_image = new_image.convert("L")

    # Apply threshold using numpy: pixels > threshold become white (255), others become black (0)
    gray_array = np.array(gray_image)
    binary_array = np.where(gray_array > threshold, 255, 0).astype(np.uint8)
    binary_image = Image.fromarray(binary_array, mode="L")

    # Convert back to RGB for consistency
    final_image = binary_image.convert("RGB")

    return final_image


def add_overlay_to_qr(
    qr_image: Image.Image,
    overlay_path: Path,
    size_percent: int = 20,
) -> Image.Image:
    """Add an overlay image to the center of a QR code.

    Args:
        qr_image: PIL Image of the QR code
        overlay_path: Path to the overlay image file
        size_percent: Size of overlay as percentage of QR code size (10-30)

    Returns:
        New PIL Image with overlay added

    Note:
        The overlay is converted to grayscale while preserving all gray levels
        (not just black and white). A white background is added behind the overlay
        to ensure it doesn't interfere with QR code reading. Transparency is
        properly handled if the overlay has an alpha channel.
    """
    try:
        # Load overlay image
        overlay = Image.open(overlay_path)
        logger.debug(f"Loaded overlay image: {overlay.size}, mode: {overlay.mode}")

        # Convert QR code to RGB if needed
        if qr_image.mode != "RGB":
            qr_image = qr_image.convert("RGB")

        # Create a copy to avoid modifying the original
        result = qr_image.copy()

        # Calculate overlay size
        qr_width, qr_height = qr_image.size
        overlay_size = int(min(qr_width, qr_height) * size_percent / 100)

        # Resize overlay maintaining aspect ratio
        overlay.thumbnail((overlay_size, overlay_size), Image.Resampling.LANCZOS)

        # Store alpha channel if present
        alpha_channel = None
        if overlay.mode == "RGBA":
            alpha_channel = overlay.split()[3]  # Extract alpha channel
            overlay = overlay.convert("RGB")  # Convert to RGB for processing

        # Convert overlay to grayscale while preserving all gray levels
        if overlay.mode != "L":
            overlay = overlay.convert("L")

        # Create a white background for the overlay area
        # This ensures the overlay doesn't break QR code scanning
        bg_size = int(overlay_size * 1.2)  # Add some padding
        white_bg = Image.new("L", (bg_size, bg_size), 255)  # White in grayscale

        # Center the overlay on the white background
        bg_x = (bg_size - overlay.width) // 2
        bg_y = (bg_size - overlay.height) // 2

        # Paste with alpha channel if it existed
        if alpha_channel:
            # Resize alpha channel to match overlay size
            alpha_channel = alpha_channel.resize(overlay.size)
            white_bg.paste(overlay, (bg_x, bg_y), alpha_channel)
        else:
            white_bg.paste(overlay, (bg_x, bg_y))

        # Convert the grayscale background to RGB for final composition
        white_bg = white_bg.convert("RGB")

        # Calculate position to center the background+overlay on QR code
        x = (qr_width - bg_size) // 2
        y = (qr_height - bg_size) // 2

        # Paste the white background with overlay onto the QR code
        result.paste(white_bg, (x, y))

        logger.info(f"Added overlay image at {size_percent}% size ({overlay_size}x{overlay_size} pixels)")
        return result

    except Exception as e:
        logger.error(f"Failed to add overlay image: {e}")
        raise ValueError(f"Could not process overlay image: {e}")


def save_qr_code(
    image: Image.Image,
    output_path: Path | str,
) -> Path:
    """Save QR code image to file.

    Args:
        image: PIL Image object
        output_path: Path to save the image

    Returns:
        Path to the saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure it's a PNG file
    if output_path.suffix.lower() != ".png":
        output_path = output_path.with_suffix(".png")

    image.save(output_path, "PNG")
    logger.info(f"Saved QR code image to: {output_path}")

    return output_path
