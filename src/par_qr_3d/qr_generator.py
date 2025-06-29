"""QR code generation module with support for different data types."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import cast

import numpy as np
import qrcode
from PIL import Image, ImageDraw
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

from .logging_config import get_logger
from .utils import ensure_rgb, load_font_with_fallbacks, prepare_output_path

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


def create_artistic_qr(
    qr_code: qrcode.QRCode,
    size: int,
    base_color: str,
    qr_color: str,
    module_style: str,
    module_size_ratio: float,
) -> Image.Image:
    """Create an artistic QR code with custom module shapes.

    Args:
        qr_code: The QRCode object with data
        size: Final image size in pixels
        base_color: Background color
        qr_color: Module color
        module_style: Style of modules (circle, dot, rounded)
        module_size_ratio: Size ratio for modules

    Returns:
        PIL Image with artistic QR code
    """
    # Get the QR code matrix
    matrix = qr_code.get_matrix()
    module_count = len(matrix)

    # Calculate module size
    module_pixels = size // (module_count + qr_code.border * 2)
    img_size = module_pixels * (module_count + qr_code.border * 2)

    # Create base image
    img = Image.new("RGB", (img_size, img_size), base_color)
    draw = ImageDraw.Draw(img)

    # Draw modules based on style
    for row in range(module_count):
        for col in range(module_count):
            if matrix[row][col]:
                # Calculate position including border
                x = (col + qr_code.border) * module_pixels
                y = (row + qr_code.border) * module_pixels

                # Calculate module center and size
                center_x = x + module_pixels // 2
                center_y = y + module_pixels // 2
                module_size = int(module_pixels * module_size_ratio)
                half_size = module_size // 2

                if module_style == "circle":
                    # Draw filled circle
                    draw.ellipse(
                        [
                            center_x - half_size,
                            center_y - half_size,
                            center_x + half_size,
                            center_y + half_size,
                        ],
                        fill=qr_color,
                    )
                elif module_style == "dot":
                    # Draw smaller filled circle (dot)
                    dot_size = int(half_size * 0.7)  # Even smaller for dot style
                    draw.ellipse(
                        [
                            center_x - dot_size,
                            center_y - dot_size,
                            center_x + dot_size,
                            center_y + dot_size,
                        ],
                        fill=qr_color,
                    )
                elif module_style == "rounded":
                    # Draw rounded square
                    radius = int(module_size * 0.25)  # 25% corner radius
                    x0 = center_x - half_size
                    y0 = center_y - half_size
                    x1 = center_x + half_size
                    y1 = center_y + half_size

                    # Use rounded rectangle if available (Pillow 8.0+)
                    try:
                        draw.rounded_rectangle(
                            [(x0, y0), (x1, y1)],
                            radius=radius,
                            fill=qr_color,
                        )
                    except AttributeError:
                        # Fallback to regular rectangle for older Pillow
                        draw.rectangle([(x0, y0), (x1, y1)], fill=qr_color)

    # Resize to final size
    if img_size != size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)

    return img


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
    base_color: str = "white",
    qr_color: str = "black",
    module_style: str = "square",
    module_size_ratio: float = 0.8,
    return_qr_object: bool = False,
    **format_kwargs: str,
) -> Image.Image | tuple[Image.Image, qrcode.QRCode]:
    """Generate a QR code image.

    Args:
        data: The data to encode
        qr_type: The type of QR code to generate
        size: The size of the QR code image in pixels (width and height)
        error_correction: Error correction level
        border: Border size in modules
        base_color: Background color (name or hex code)
        qr_color: QR code module color (name or hex code)
        module_style: Style of QR modules (square, circle, dot, rounded)
        module_size_ratio: Size ratio for styled modules (0.5-1.0)
        return_qr_object: If True, also return the QRCode object
        **format_kwargs: Additional parameters for specific QR types

    Returns:
        PIL Image object containing the QR code, or tuple of (image, qr_object) if return_qr_object is True
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

    # Create basic QR code image
    if module_style == "square":
        # Standard square modules
        img = qr.make_image(fill_color=qr_color, back_color=base_color)
        pil_img = cast(Image.Image, img)
        pil_img = pil_img.resize((size, size), Image.Resampling.NEAREST)
    else:
        # Create artistic pattern
        pil_img = create_artistic_qr(qr, size, base_color, qr_color, module_style, module_size_ratio)

    logger.info(
        f"Generated QR code: {size}x{size}px, style: {module_style}, error correction: {error_correction.value}"
    )

    if return_qr_object:
        return pil_img, qr
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

    # Load font for clear 3D printing
    actual_font_size = 16  # Use 16px for better readability in 3D prints

    # Load font with bundled fonts prioritized
    font = load_font_with_fallbacks(
        font_size=actual_font_size,
        use_bold=True,
        text=label,  # Pass label text to check for emoji
    )

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


def add_center_text_to_qr(
    qr_image: Image.Image,
    text: str,
    font_size: int = 24,
    font_name: str = "DejaVuSans.ttf",
    size_percent: int = 20,
    text_color: str = "black",
    bg_color: str = "white",
    convert_to_grayscale: bool = True,
) -> Image.Image:
    """Add text or emoji to the center of a QR code.

    Args:
        qr_image: PIL Image of the QR code
        text: Text or emoji to display
        font_size: Font size in pixels
        font_name: Font name (must support emoji for emoji text)
        size_percent: Size of text area as percentage of QR code size (10-30)
        text_color: Color of the text
        bg_color: Background color behind text
        convert_to_grayscale: If True, convert to grayscale (default for STL)

    Returns:
        New PIL Image with text added to center
    """
    from PIL import ImageDraw

    # Convert QR code to RGB if needed
    qr_image = ensure_rgb(qr_image)

    # Create a copy to avoid modifying the original
    result = qr_image.copy()

    # Calculate text area size
    qr_width, qr_height = qr_image.size
    text_area_size = int(min(qr_width, qr_height) * size_percent / 100)

    # Load font with fallbacks, prioritizing emoji fonts if needed
    font = load_font_with_fallbacks(font_size=font_size, font_name=font_name, text=text)

    # Create text image with background
    text_img = Image.new("RGB", (text_area_size, text_area_size), bg_color)
    draw = ImageDraw.Draw(text_img)

    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # If text is too large, adjust font size
    if text_width > text_area_size * 0.9 or text_height > text_area_size * 0.9:
        scale_factor = min((text_area_size * 0.9) / text_width, (text_area_size * 0.9) / text_height)
        new_font_size = int(font_size * scale_factor)
        # Reload font with new size
        font = load_font_with_fallbacks(font_size=new_font_size, font_name=font_name, text=text)
        # Recalculate bbox
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

    # Center the text
    x = (text_area_size - text_width) // 2
    y = (text_area_size - text_height) // 2

    # Draw the text
    draw.text((x, y), text, fill=text_color, font=font)

    # Convert to grayscale if requested
    if convert_to_grayscale:
        text_img = text_img.convert("L").convert("RGB")

    # Calculate position to center on QR code
    x_pos = (qr_width - text_area_size) // 2
    y_pos = (qr_height - text_area_size) // 2

    # Paste text image onto QR code
    result.paste(text_img, (x_pos, y_pos))

    mode_str = "grayscale" if convert_to_grayscale else "color"
    logger.info(f"Added {mode_str} text '{text}' at {size_percent}% size")
    return result


def add_overlay_to_qr(
    qr_image: Image.Image,
    overlay_path: Path,
    size_percent: int = 20,
    convert_to_grayscale: bool = True,
) -> Image.Image:
    """Add an overlay image to the center of a QR code.

    Args:
        qr_image: PIL Image of the QR code
        overlay_path: Path to the overlay image file
        size_percent: Size of overlay as percentage of QR code size (10-30)
        convert_to_grayscale: If True, convert overlay to grayscale (default for STL)

    Returns:
        New PIL Image with overlay added

    Note:
        When convert_to_grayscale is True, the overlay is converted to grayscale
        while preserving all gray levels (not just black and white). When False,
        the overlay retains its original colors. A white background is added behind
        the overlay to ensure it doesn't interfere with QR code reading. Transparency
        is properly handled if the overlay has an alpha channel.
    """
    try:
        # Load overlay image
        overlay = Image.open(overlay_path)
        logger.debug(f"Loaded overlay image: {overlay.size}, mode: {overlay.mode}")

        # Convert QR code to RGB if needed
        qr_image = ensure_rgb(qr_image)

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

        # Convert overlay to grayscale if requested (for STL generation)
        if convert_to_grayscale and overlay.mode != "L":
            overlay = overlay.convert("L")

        # Create a white background for the overlay area
        # This ensures the overlay doesn't break QR code scanning
        bg_size = int(overlay_size * 1.2)  # Add some padding

        # Create background in appropriate mode
        if convert_to_grayscale and overlay.mode == "L":
            white_bg = Image.new("L", (bg_size, bg_size), 255)  # White in grayscale
        else:
            white_bg = Image.new("RGB", (bg_size, bg_size), "white")  # White in RGB

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

        # Convert to RGB for final composition if needed
        if white_bg.mode != "RGB":
            white_bg = white_bg.convert("RGB")

        # Calculate position to center the background+overlay on QR code
        x = (qr_width - bg_size) // 2
        y = (qr_height - bg_size) // 2

        # Paste the white background with overlay onto the QR code
        result.paste(white_bg, (x, y))

        mode_str = "grayscale" if convert_to_grayscale else "color"
        logger.info(f"Added {mode_str} overlay image at {size_percent}% size ({overlay_size}x{overlay_size} pixels)")
        return result

    except Exception as e:
        logger.error(f"Failed to add overlay image: {e}")
        raise ValueError(f"Could not process overlay image: {e}")


def add_frame_to_qr(
    qr_image: Image.Image,
    frame_style: str,
    frame_width: int = 10,
    frame_color: str = "black",
) -> Image.Image:
    """Add a decorative frame around a QR code.

    Args:
        qr_image: PIL Image of the QR code
        frame_style: Style of frame (square, rounded, hexagon, octagon)
        frame_width: Width of the frame border in pixels
        frame_color: Color of the frame (name or hex code)

    Returns:
        New PIL Image with frame added

    Note:
        The frame is added as a border around the QR code. Different styles
        create different shapes, with the QR code centered within. The frame
        color can be any valid PIL color name or hex code.
    """
    # Convert to RGB if needed
    if qr_image.mode != "RGB":
        qr_image = qr_image.convert("RGB")

    # Get original dimensions
    orig_width, orig_height = qr_image.size

    # Calculate new dimensions with frame
    new_width = orig_width + (frame_width * 2)
    new_height = orig_height + (frame_width * 2)

    # Create new image with frame color background
    framed_image = Image.new("RGB", (new_width, new_height), frame_color)

    if frame_style == "square":
        # Simple square frame - just paste QR in center
        framed_image.paste(qr_image, (frame_width, frame_width))

    elif frame_style == "rounded":
        # Create rounded corners
        # First paste the QR code
        framed_image.paste(qr_image, (frame_width, frame_width))

        # Create a mask for rounded corners
        mask = Image.new("L", (new_width, new_height), 0)
        draw = ImageDraw.Draw(mask)

        # Calculate corner radius (20% of frame width)
        corner_radius = int(frame_width * 2)

        # Draw rounded rectangle on mask
        draw.rounded_rectangle([(0, 0), (new_width - 1, new_height - 1)], radius=corner_radius, fill=255)

        # Create a white background and composite
        white_bg = Image.new("RGB", (new_width, new_height), "white")
        framed_image = Image.composite(framed_image, white_bg, mask)

    elif frame_style == "hexagon":
        # Create hexagonal frame
        # First paste the QR code
        framed_image.paste(qr_image, (frame_width, frame_width))

        # Create a mask for hexagon
        mask = Image.new("L", (new_width, new_height), 0)
        draw = ImageDraw.Draw(mask)

        # Calculate hexagon points
        cx, cy = new_width // 2, new_height // 2
        size = min(new_width, new_height) // 2

        # Hexagon has 6 points
        points = []
        for i in range(6):
            angle = np.pi / 3 * i  # 60 degrees
            x = cx + size * np.cos(angle)
            y = cy + size * np.sin(angle)
            points.append((x, y))

        # Draw hexagon on mask
        draw.polygon(points, fill=255)

        # Create a white background and composite
        white_bg = Image.new("RGB", (new_width, new_height), "white")
        framed_image = Image.composite(framed_image, white_bg, mask)

    elif frame_style == "octagon":
        # Create octagonal frame
        # First paste the QR code
        framed_image.paste(qr_image, (frame_width, frame_width))

        # Create a mask for octagon
        mask = Image.new("L", (new_width, new_height), 0)
        draw = ImageDraw.Draw(mask)

        # Calculate octagon points
        cx, cy = new_width // 2, new_height // 2
        size = min(new_width, new_height) // 2

        # Octagon has 8 points
        points = []
        for i in range(8):
            angle = np.pi / 4 * i  # 45 degrees
            x = cx + size * np.cos(angle)
            y = cy + size * np.sin(angle)
            points.append((x, y))

        # Draw octagon on mask
        draw.polygon(points, fill=255)

        # Create a white background and composite
        white_bg = Image.new("RGB", (new_width, new_height), "white")
        framed_image = Image.composite(framed_image, white_bg, mask)

    logger.info(f"Added {frame_style} frame: {frame_width}px width, {frame_color} color")
    return framed_image


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
    # Prepare output path with .png extension
    output_path = prepare_output_path(output_path, ".png")

    image.save(output_path, "PNG")
    logger.info(f"Saved QR code image to: {output_path}")

    return output_path


def generate_qr_svg(
    qr_code: qrcode.QRCode,
    base_color: str = "white",
    qr_color: str = "black",
    module_style: str = "square",
    module_size_ratio: float = 0.8,
) -> str:
    """Generate SVG string from QR code.

    Args:
        qr_code: The QRCode object with data
        base_color: Background color
        qr_color: Module color
        module_style: Style of modules (square, circle, dot, rounded)
        module_size_ratio: Size ratio for modules

    Returns:
        SVG string representation of the QR code
    """
    # Get the QR code matrix
    matrix = qr_code.get_matrix()
    module_count = len(matrix)

    # Calculate SVG dimensions
    border = qr_code.border
    svg_size = (module_count + 2 * border) * 10  # 10 units per module

    # Start SVG
    svg_parts = [
        f'<svg width="{svg_size}" height="{svg_size}" version="1.1" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{svg_size}" height="{svg_size}" fill="{base_color}"/>',
    ]

    # Draw modules
    module_size = 10
    adjusted_size = module_size * module_size_ratio
    offset = (module_size - adjusted_size) / 2

    for row_idx, row in enumerate(matrix):
        for col_idx, module in enumerate(row):
            if module:
                x = (col_idx + border) * module_size
                y = (row_idx + border) * module_size

                if module_style == "square":
                    svg_parts.append(
                        f'<rect x="{x}" y="{y}" width="{module_size}" height="{module_size}" fill="{qr_color}"/>'
                    )
                elif module_style == "circle":
                    cx = x + module_size / 2
                    cy = y + module_size / 2
                    r = adjusted_size / 2
                    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{qr_color}"/>')
                elif module_style == "dot":
                    cx = x + module_size / 2
                    cy = y + module_size / 2
                    r = adjusted_size / 2
                    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{qr_color}"/>')
                elif module_style == "rounded":
                    rx = adjusted_size * 0.2
                    svg_parts.append(
                        f'<rect x="{x + offset}" y="{y + offset}" width="{adjusted_size}" '
                        f'height="{adjusted_size}" rx="{rx}" fill="{qr_color}"/>'
                    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def save_qr_svg(
    qr_code: qrcode.QRCode,
    output_path: Path | str,
    base_color: str = "white",
    qr_color: str = "black",
    module_style: str = "square",
    module_size_ratio: float = 0.8,
) -> Path:
    """Save QR code as SVG file.

    Args:
        qr_code: The QRCode object with data
        output_path: Path to save the SVG
        base_color: Background color
        qr_color: Module color
        module_style: Style of modules
        module_size_ratio: Size ratio for modules

    Returns:
        Path to the saved SVG file
    """
    # Prepare output path with .svg extension
    output_path = prepare_output_path(output_path, ".svg")

    # Generate SVG
    svg_content = generate_qr_svg(qr_code, base_color, qr_color, module_style, module_size_ratio)

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    logger.info(f"Saved QR code SVG to: {output_path}")
    return output_path
