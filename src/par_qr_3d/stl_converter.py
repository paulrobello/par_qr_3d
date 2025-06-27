"""Convert QR code images to 3D STL models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from stl import mesh  # type: ignore[import-untyped]

from .logging_config import get_logger

logger = get_logger(__name__)


def image_to_3d_array(
    image: Image.Image,
    base_height: float = 2.0,
    qr_height: float = 2.0,
    invert: bool = False,
) -> np.ndarray:
    """Convert a QR code image to a 3D height map array.

    Args:
        image: PIL Image of the QR code
        base_height: Height of the solid base plate in mm
        qr_height: Additional height for QR code modules in mm (black areas extend this much above base)
        invert: If True, black areas are recessed and white areas are raised

    Returns:
        3D numpy array representing heights from z=0 with solid base
    """
    # Convert to grayscale if needed
    if image.mode != "L":
        image = image.convert("L")

    # Convert to numpy array
    img_array = np.array(image)

    # Normalize to 0-1
    img_array = img_array / 255.0

    # Invert if requested
    if invert:
        img_array = 1.0 - img_array

    # Create height map
    # All areas have at least base_height (solid base plate)
    # Black pixels (0) get additional qr_height on top of base
    # White pixels (1) stay at base height
    # This creates a solid base with QR pattern extruded on top
    height_map = np.full_like(img_array, base_height, dtype=float)
    # Add QR height to black areas (where img_array is 0)
    height_map = height_map + (1.0 - img_array) * qr_height

    return height_map


def create_stl_from_heightmap(
    height_map: np.ndarray,
    pixel_size: float = 1.0,
) -> Any:
    """Create an STL mesh from a height map.

    Args:
        height_map: 2D array of heights
        pixel_size: Size of each pixel in mm

    Returns:
        STL Mesh object
    """
    height, width = height_map.shape

    # We need to count faces more carefully
    # Top surface: 2 triangles per pixel
    num_faces = height * width * 2

    # Bottom surface: 2 triangles for entire base
    num_faces += 2

    # Outer walls: 2 triangles per edge pixel
    num_faces += 2 * (2 * height + 2 * width)

    # Internal walls: We need walls at every height transition
    # Count transitions between adjacent pixels
    for y in range(height):
        for x in range(width):
            curr_height = height_map[y, x]
            # Check right neighbor
            if x < width - 1 and height_map[y, x + 1] != curr_height:
                num_faces += 2  # Two triangles for vertical wall
            # Check bottom neighbor
            if y < height - 1 and height_map[y + 1, x] != curr_height:
                num_faces += 2  # Two triangles for vertical wall

    # Create mesh
    stl_mesh: Any = mesh.Mesh(np.zeros(num_faces, dtype=mesh.Mesh.dtype))

    face_idx = 0

    # Create top surface
    for y in range(height):
        for x in range(width):
            # Get the four corners of this pixel
            x0, y0 = x * pixel_size, y * pixel_size
            x1, y1 = (x + 1) * pixel_size, (y + 1) * pixel_size

            # Height for this pixel
            h = height_map[y, x]

            # First triangle
            stl_mesh.vectors[face_idx] = np.array([[x0, y0, h], [x1, y0, h], [x0, y1, h]])
            face_idx += 1

            # Second triangle
            stl_mesh.vectors[face_idx] = np.array([[x1, y0, h], [x1, y1, h], [x0, y1, h]])
            face_idx += 1

    # Create internal walls at height transitions
    for y in range(height):
        for x in range(width):
            x0, y0 = x * pixel_size, y * pixel_size
            x1, y1 = (x + 1) * pixel_size, (y + 1) * pixel_size
            curr_height = height_map[y, x]

            # Check right neighbor - create vertical wall if heights differ
            if x < width - 1:
                right_height = height_map[y, x + 1]
                if curr_height != right_height:
                    # Create wall between current and right pixel
                    # Wall goes from min height to max height
                    min_h = min(curr_height, right_height)
                    max_h = max(curr_height, right_height)

                    # Two triangles forming a vertical rectangle
                    if curr_height > right_height:
                        # Current is higher, normal points left
                        stl_mesh.vectors[face_idx] = np.array([[x1, y0, min_h], [x1, y1, min_h], [x1, y0, max_h]])
                        face_idx += 1

                        stl_mesh.vectors[face_idx] = np.array([[x1, y1, min_h], [x1, y1, max_h], [x1, y0, max_h]])
                        face_idx += 1
                    else:
                        # Right is higher, normal points right
                        stl_mesh.vectors[face_idx] = np.array([[x1, y0, min_h], [x1, y0, max_h], [x1, y1, min_h]])
                        face_idx += 1

                        stl_mesh.vectors[face_idx] = np.array([[x1, y0, max_h], [x1, y1, max_h], [x1, y1, min_h]])
                        face_idx += 1

            # Check bottom neighbor - create vertical wall if heights differ
            if y < height - 1:
                bottom_height = height_map[y + 1, x]
                if curr_height != bottom_height:
                    # Create wall between current and bottom pixel
                    # Wall goes from min height to max height
                    min_h = min(curr_height, bottom_height)
                    max_h = max(curr_height, bottom_height)

                    # Two triangles forming a vertical rectangle
                    if curr_height > bottom_height:
                        # Current is higher, normal points up
                        stl_mesh.vectors[face_idx] = np.array([[x0, y1, min_h], [x1, y1, min_h], [x0, y1, max_h]])
                        face_idx += 1

                        stl_mesh.vectors[face_idx] = np.array([[x1, y1, min_h], [x1, y1, max_h], [x0, y1, max_h]])
                        face_idx += 1
                    else:
                        # Bottom is higher, normal points down
                        stl_mesh.vectors[face_idx] = np.array([[x0, y1, min_h], [x0, y1, max_h], [x1, y1, min_h]])
                        face_idx += 1

                        stl_mesh.vectors[face_idx] = np.array([[x0, y1, max_h], [x1, y1, max_h], [x1, y1, min_h]])
                        face_idx += 1

    # Create outer walls
    total_width = width * pixel_size
    total_height = height * pixel_size

    # Front side (y=0)
    for x in range(width):
        x0, x1 = x * pixel_size, (x + 1) * pixel_size
        h = height_map[0, x]

        # Two triangles
        stl_mesh.vectors[face_idx] = np.array([[x0, 0, 0], [x1, 0, 0], [x0, 0, h]])
        face_idx += 1
        stl_mesh.vectors[face_idx] = np.array([[x1, 0, 0], [x1, 0, h], [x0, 0, h]])
        face_idx += 1

    # Back side (y=max)
    for x in range(width):
        x0, x1 = x * pixel_size, (x + 1) * pixel_size
        h = height_map[height - 1, x]

        # Two triangles
        stl_mesh.vectors[face_idx] = np.array([[x0, total_height, h], [x1, total_height, h], [x0, total_height, 0]])
        face_idx += 1
        stl_mesh.vectors[face_idx] = np.array([[x1, total_height, h], [x1, total_height, 0], [x0, total_height, 0]])
        face_idx += 1

    # Left side (x=0)
    for y in range(height):
        y0, y1 = y * pixel_size, (y + 1) * pixel_size
        h = height_map[y, 0]

        # Two triangles
        stl_mesh.vectors[face_idx] = np.array([[0, y0, h], [0, y1, h], [0, y0, 0]])
        face_idx += 1
        stl_mesh.vectors[face_idx] = np.array([[0, y1, h], [0, y1, 0], [0, y0, 0]])
        face_idx += 1

    # Right side (x=max)
    for y in range(height):
        y0, y1 = y * pixel_size, (y + 1) * pixel_size
        h = height_map[y, width - 1]

        # Two triangles
        stl_mesh.vectors[face_idx] = np.array([[total_width, y0, 0], [total_width, y1, 0], [total_width, y0, h]])
        face_idx += 1
        stl_mesh.vectors[face_idx] = np.array([[total_width, y1, 0], [total_width, y1, h], [total_width, y0, h]])
        face_idx += 1

    # Bottom face - solid base covering entire area
    stl_mesh.vectors[face_idx] = np.array([[0, 0, 0], [total_width, 0, 0], [0, total_height, 0]])
    face_idx += 1
    stl_mesh.vectors[face_idx] = np.array([[total_width, 0, 0], [total_width, total_height, 0], [0, total_height, 0]])
    face_idx += 1

    # Update normals
    stl_mesh.update_normals()

    logger.info(f"Created STL mesh with {face_idx} faces")
    return stl_mesh


def convert_qr_to_stl(
    qr_image: Image.Image,
    output_path: Path | str,
    base_size_mm: tuple[float, float] = (50.0, 50.0),
    base_height_mm: float = 2.0,
    qr_height_mm: float = 2.0,
    invert: bool = False,
) -> Path:
    """Convert a QR code image to an STL file.

    Args:
        qr_image: PIL Image of the QR code
        output_path: Path to save the STL file
        base_size_mm: Size of the base in mm (width, height)
        base_height_mm: Height of the base layer in mm
        qr_height_mm: Additional height for QR code modules in mm
        invert: If True, white areas are raised instead of black

    Returns:
        Path to the saved STL file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure it's an STL file
    if output_path.suffix.lower() != ".stl":
        output_path = output_path.with_suffix(".stl")

    # Convert image to height map
    height_map = image_to_3d_array(
        qr_image,
        base_height=base_height_mm,
        qr_height=qr_height_mm,
        invert=invert,
    )

    # Flip the height map vertically to correct the orientation
    # This ensures labels at the top of the image appear at the top of the STL
    height_map = np.flipud(height_map)

    # Calculate pixel size to achieve desired base size
    img_height, img_width = height_map.shape
    pixel_size_x = base_size_mm[0] / img_width
    pixel_size_y = base_size_mm[1] / img_height

    # Use uniform pixel size (average of x and y)
    pixel_size = (pixel_size_x + pixel_size_y) / 2

    logger.debug(f"Image size: {img_width}x{img_height}, pixel size: {pixel_size:.3f}mm")

    # Create STL mesh
    stl_mesh = create_stl_from_heightmap(height_map, pixel_size=pixel_size)

    # Save STL file
    stl_mesh.save(str(output_path))

    total_height = base_height_mm + qr_height_mm
    logger.info(f"Saved STL file to: {output_path}")
    logger.info(f"Model dimensions: {base_size_mm[0]:.1f} x {base_size_mm[1]:.1f} x {total_height:.1f} mm")

    return output_path
