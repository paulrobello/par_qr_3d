"""Utility modules for par_qr_3d."""

from .color_utils import color_to_3mf_format, normalize_rgb, parse_color
from .font_utils import contains_emoji, load_font_with_fallbacks
from .image_utils import ensure_grayscale, ensure_rgb
from .mesh_utils import check_mesh_from_stl, numpy_mesh_to_trimesh, repair_mesh, save_mesh_debug_view, validate_mesh
from .path_utils import ensure_file_extension, prepare_output_path
from .platform_utils import open_file_in_default_app
from .validation_utils import validate_choice, validate_conflict

__all__ = [
    "parse_color",
    "normalize_rgb",
    "color_to_3mf_format",
    "contains_emoji",
    "load_font_with_fallbacks",
    "ensure_grayscale",
    "ensure_rgb",
    "ensure_file_extension",
    "prepare_output_path",
    "open_file_in_default_app",
    "validate_choice",
    "validate_conflict",
    "validate_mesh",
    "repair_mesh",
    "numpy_mesh_to_trimesh",
    "save_mesh_debug_view",
    "check_mesh_from_stl",
]
