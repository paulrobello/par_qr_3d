"""Convert QR code images to 3D STL models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from stl import mesh  # type: ignore[import-untyped]

try:
    import lib3mf
    from lib3mf import get_wrapper

    HAS_LIB3MF = True
except ImportError:
    HAS_LIB3MF = False

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


def convert_qr_to_3mf(
    qr_image: Image.Image,
    output_path: Path | str,
    base_size_mm: tuple[float, float] = (50.0, 50.0),
    base_height_mm: float = 2.0,
    qr_height_mm: float = 2.0,
    invert: bool = False,
    base_color: str = "white",
    qr_color: str = "black",
    separate_components: bool = False,
) -> Path:
    """Convert a QR code image to a 3MF file with color support using lib3mf.

    Args:
        qr_image: PIL Image of the QR code
        output_path: Path to save the 3MF file
        base_size_mm: Size of the base in mm (width, height)
        base_height_mm: Height of the base layer in mm
        qr_height_mm: Additional height for QR code modules in mm
        invert: If True, white areas are raised instead of black
        base_color: Color name or hex code for the base/background
        qr_color: Color name or hex code for the QR modules
        separate_components: If True, create separate objects for each color

    Returns:
        Path to the saved 3MF file
    """
    if not HAS_LIB3MF:
        raise ImportError("lib3mf is required for colored 3MF export. Install with: pip install lib3mf")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure it's a 3MF file
    if output_path.suffix.lower() != ".3mf":
        output_path = output_path.with_suffix(".3mf")

    # Convert colors to RGB
    from PIL import ImageColor

    try:
        base_rgb = ImageColor.getrgb(base_color)
    except ValueError:
        logger.warning(f"Invalid base color '{base_color}', using white")
        base_rgb = (255, 255, 255)

    try:
        qr_rgb = ImageColor.getrgb(qr_color)
    except ValueError:
        logger.warning(f"Invalid QR color '{qr_color}', using black")
        qr_rgb = (0, 0, 0)

    # Convert image to height map
    height_map = image_to_3d_array(
        qr_image,
        base_height=base_height_mm,
        qr_height=qr_height_mm,
        invert=invert,
    )

    # Flip the height map vertically to correct the orientation
    height_map = np.flipud(height_map)

    # Calculate pixel size to achieve desired base size
    img_height, img_width = height_map.shape
    pixel_size_x = base_size_mm[0] / img_width
    pixel_size_y = base_size_mm[1] / img_height
    pixel_size = (pixel_size_x + pixel_size_y) / 2

    logger.debug(f"Image size: {img_width}x{img_height}, pixel size: {pixel_size:.3f}mm")

    # Initialize lib3mf
    wrapper = get_wrapper()
    model = wrapper.CreateModel()  # type: ignore[attr-defined]

    if separate_components:
        # Create separate mesh objects for each color
        base_mesh = model.AddMeshObject()  # type: ignore[attr-defined]
        base_mesh.SetName("Base")

        qr_mesh = model.AddMeshObject()  # type: ignore[attr-defined]
        qr_mesh.SetName("QR Modules")

        # Create color group for separate components
        color_group = model.AddColorGroup()  # type: ignore[attr-defined]

        # Add colors
        base_color_id = color_group.AddColor(
            wrapper.FloatRGBAToColor(base_rgb[0] / 255.0, base_rgb[1] / 255.0, base_rgb[2] / 255.0, 1.0)
        )
        qr_color_id = color_group.AddColor(
            wrapper.FloatRGBAToColor(qr_rgb[0] / 255.0, qr_rgb[1] / 255.0, qr_rgb[2] / 255.0, 1.0)
        )

        # Set object colors
        base_mesh.SetObjectLevelProperty(color_group.GetResourceID(), base_color_id)
        qr_mesh.SetObjectLevelProperty(color_group.GetResourceID(), qr_color_id)
    else:
        # Single object with material group
        material_group = model.AddBaseMaterialGroup()  # type: ignore[attr-defined]

        # Add materials with colors
        base_material_id = material_group.AddMaterial(
            f"{base_color} base",
            wrapper.FloatRGBAToColor(base_rgb[0] / 255.0, base_rgb[1] / 255.0, base_rgb[2] / 255.0, 1.0),
        )
        qr_material_id = material_group.AddMaterial(
            f"{qr_color} QR",
            wrapper.FloatRGBAToColor(qr_rgb[0] / 255.0, qr_rgb[1] / 255.0, qr_rgb[2] / 255.0, 1.0),
        )

        # Create single mesh object
        mesh_object = model.AddMeshObject()  # type: ignore[attr-defined]
        mesh_object.SetName("QR Code")
        triangle_properties = []

    # Build QR modules
    for y in range(img_height):
        for x in range(img_width):
            x0, y0 = x * pixel_size, y * pixel_size
            x1, y1 = (x + 1) * pixel_size, (y + 1) * pixel_size
            z0 = base_height_mm  # Start from base height
            z1 = height_map[y, x]

            # Skip if this pixel is at base height (no need to create a box)
            if abs(z1 - base_height_mm) < 0.001:
                continue

            # Choose which mesh to add to
            current_mesh = qr_mesh if separate_components else mesh_object

            # Add 8 vertices for the box
            vertices_indices = []
            for vx, vy, vz in [
                (x0, y0, z0),
                (x1, y0, z0),
                (x1, y1, z0),
                (x0, y1, z0),
                (x0, y0, z1),
                (x1, y0, z1),
                (x1, y1, z1),
                (x0, y1, z1),
            ]:
                position = lib3mf.Position()
                position.Coordinates[0] = float(vx)
                position.Coordinates[1] = float(vy)
                position.Coordinates[2] = float(vz)
                vertices_indices.append(current_mesh.AddVertex(position))

            # Create triangles for the box (12 triangles, 2 per face)
            triangle_indices = [
                # Bottom face
                (0, 2, 1),
                (0, 3, 2),
                # Top face
                (4, 5, 6),
                (4, 6, 7),
                # Front face
                (0, 1, 5),
                (0, 5, 4),
                # Back face
                (3, 7, 6),
                (3, 6, 2),
                # Left face
                (0, 4, 7),
                (0, 7, 3),
                # Right face
                (1, 2, 6),
                (1, 6, 5),
            ]

            # Add triangles and set material
            for v0, v1, v2 in triangle_indices:
                triangle = lib3mf.Triangle()
                triangle.Indices[0] = vertices_indices[v0]
                triangle.Indices[1] = vertices_indices[v1]
                triangle.Indices[2] = vertices_indices[v2]
                current_mesh.AddTriangle(triangle)

                if not separate_components:
                    # Create triangle properties with QR material
                    prop = lib3mf.TriangleProperties()
                    prop.ResourceID = material_group.GetResourceID()
                    prop.PropertyIDs[0] = qr_material_id
                    prop.PropertyIDs[1] = qr_material_id
                    prop.PropertyIDs[2] = qr_material_id
                    triangle_properties.append(prop)

    # Add complete base plate as a box
    base_width = img_width * pixel_size
    base_depth = img_height * pixel_size

    # Choose which mesh to add base to
    base_target_mesh = base_mesh if separate_components else mesh_object

    # Create 8 vertices for the base box
    base_vertices = []
    for vx, vy, vz in [
        (0, 0, 0),  # 0: bottom-left-bottom
        (base_width, 0, 0),  # 1: bottom-right-bottom
        (base_width, base_depth, 0),  # 2: top-right-bottom
        (0, base_depth, 0),  # 3: top-left-bottom
        (0, 0, base_height_mm),  # 4: bottom-left-top
        (base_width, 0, base_height_mm),  # 5: bottom-right-top
        (base_width, base_depth, base_height_mm),  # 6: top-right-top
        (0, base_depth, base_height_mm),  # 7: top-left-top
    ]:
        position = lib3mf.Position()
        position.Coordinates[0] = float(vx)
        position.Coordinates[1] = float(vy)
        position.Coordinates[2] = float(vz)
        base_vertices.append(base_target_mesh.AddVertex(position))

    # Create triangles for all 6 faces of the base box
    base_triangle_indices = [
        # Bottom face
        (0, 2, 1),
        (0, 3, 2),
        # Top face
        (4, 5, 6),
        (4, 6, 7),
        # Front face
        (0, 1, 5),
        (0, 5, 4),
        # Back face
        (3, 7, 6),
        (3, 6, 2),
        # Left face
        (0, 4, 7),
        (0, 7, 3),
        # Right face
        (1, 2, 6),
        (1, 6, 5),
    ]

    for v0, v1, v2 in base_triangle_indices:
        triangle = lib3mf.Triangle()
        triangle.Indices[0] = base_vertices[v0]
        triangle.Indices[1] = base_vertices[v1]
        triangle.Indices[2] = base_vertices[v2]
        base_target_mesh.AddTriangle(triangle)

        if not separate_components:
            # Create triangle properties with base material
            prop = lib3mf.TriangleProperties()
            prop.ResourceID = material_group.GetResourceID()
            prop.PropertyIDs[0] = base_material_id
            prop.PropertyIDs[1] = base_material_id
            prop.PropertyIDs[2] = base_material_id
            triangle_properties.append(prop)

    # Apply properties and add build items
    if separate_components:
        # Add both meshes as build items
        model.AddBuildItem(base_mesh, wrapper.GetIdentityTransform())  # type: ignore[attr-defined]
        model.AddBuildItem(qr_mesh, wrapper.GetIdentityTransform())  # type: ignore[attr-defined]
    else:
        # Apply all triangle properties to single mesh
        mesh_object.SetAllTriangleProperties(triangle_properties)
        # Add single build item
        model.AddBuildItem(mesh_object, wrapper.GetIdentityTransform())  # type: ignore[attr-defined]

    # Write to file
    writer = model.QueryWriter("3mf")  # type: ignore[attr-defined]
    writer.WriteToFile(str(output_path))

    total_height = base_height_mm + qr_height_mm
    logger.info(f"Saved 3MF file to: {output_path}")
    logger.info(f"Model dimensions: {base_size_mm[0]:.1f} x {base_size_mm[1]:.1f} x {total_height:.1f} mm")
    logger.info(f"Colors: base={base_color}, QR={qr_color}")

    return output_path
