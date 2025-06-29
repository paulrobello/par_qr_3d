"""Utilities for mesh validation and repair using trimesh."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import trimesh


def validate_mesh(mesh: trimesh.Trimesh, verbose: bool = False) -> dict[str, Any]:
    """Validate a mesh and return diagnostic information.

    Args:
        mesh: The trimesh object to validate
        verbose: If True, print detailed diagnostics

    Returns:
        Dictionary containing validation results
    """
    # Get basic mesh properties
    results = {
        "is_watertight": mesh.is_watertight,
        "is_winding_consistent": mesh.is_winding_consistent,
        "is_volume": mesh.is_volume,
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.faces),
        "euler_number": mesh.euler_number,
        "duplicate_faces": 0,
        "degenerate_faces": 0,
        "unreferenced_vertices": 0,
        "non_manifold_edges": 0,
    }

    # Check for edge manifold property
    try:
        # Get edges and their face adjacency
        edges_face = mesh.edges_face

        # Count how many faces each edge belongs to
        edge_face_count = np.bincount(edges_face.flatten())

        # Non-manifold edges have != 2 adjacent faces
        # (1 face = boundary edge, >2 faces = non-manifold)
        non_manifold_mask = edge_face_count != 2
        non_manifold_count = np.sum(non_manifold_mask)

        results["non_manifold_edges"] = int(non_manifold_count)
        results["is_edge_manifold"] = non_manifold_count == 0
    except Exception:
        # Fallback if edge calculation fails
        results["non_manifold_edges"] = -1
        results["is_edge_manifold"] = False

    # Check for duplicate faces
    unique_faces = {tuple(sorted(face)) for face in mesh.faces}
    results["duplicate_faces"] = len(mesh.faces) - len(unique_faces)

    # Check for degenerate faces (faces with duplicate vertices)
    degenerate_count = 0
    for face in mesh.faces:
        if len(set(face)) < 3:
            degenerate_count += 1
    results["degenerate_faces"] = degenerate_count

    # Check for unreferenced vertices
    referenced_vertices = set(mesh.faces.flatten())
    all_vertices = set(range(len(mesh.vertices)))
    results["unreferenced_vertices"] = len(all_vertices - referenced_vertices)

    if verbose:
        print("=== Mesh Validation Results ===")
        print(f"Watertight: {results['is_watertight']}")
        print(f"Edge manifold: {results['is_edge_manifold']}")
        print(f"Winding consistent: {results['is_winding_consistent']}")
        print(f"Valid volume: {results['is_volume']}")
        print(f"Vertices: {results['vertex_count']}")
        print(f"Faces: {results['face_count']}")
        print(f"Euler number: {results['euler_number']}")
        print(f"Non-manifold edges: {results['non_manifold_edges']}")
        print(f"Duplicate faces: {results['duplicate_faces']}")
        print(f"Degenerate faces: {results['degenerate_faces']}")
        print(f"Unreferenced vertices: {results['unreferenced_vertices']}")

    return results


def repair_mesh(mesh: trimesh.Trimesh, verbose: bool = False) -> trimesh.Trimesh:
    """Repair common mesh issues.

    Args:
        mesh: The trimesh object to repair
        verbose: If True, print repair operations

    Returns:
        Repaired mesh
    """
    if verbose:
        print("\n=== Mesh Repair ===")

    # Remove duplicate vertices
    original_vertex_count = len(mesh.vertices)
    mesh.merge_vertices()
    if verbose and len(mesh.vertices) < original_vertex_count:
        print(f"Merged {original_vertex_count - len(mesh.vertices)} duplicate vertices")

    # Remove duplicate faces
    original_face_count = len(mesh.faces)
    mesh.remove_duplicate_faces()
    if verbose and len(mesh.faces) < original_face_count:
        print(f"Removed {original_face_count - len(mesh.faces)} duplicate faces")

    # Remove degenerate faces
    original_face_count = len(mesh.faces)
    mesh.remove_degenerate_faces()
    if verbose and len(mesh.faces) < original_face_count:
        print(f"Removed {original_face_count - len(mesh.faces)} degenerate faces")

    # Remove unreferenced vertices
    original_vertex_count = len(mesh.vertices)
    mesh.remove_unreferenced_vertices()
    if verbose and len(mesh.vertices) < original_vertex_count:
        print(f"Removed {original_vertex_count - len(mesh.vertices)} unreferenced vertices")

    # Fix normals if needed
    if not mesh.is_winding_consistent:
        mesh.fix_normals()
        if verbose:
            print("Fixed inconsistent face winding")

    # Fill holes if the mesh is not watertight
    if not mesh.is_watertight:
        try:
            mesh.fill_holes()
            if verbose:
                print("Attempted to fill holes")
        except Exception:
            if verbose:
                print("Could not fill all holes")

    return mesh


def numpy_mesh_to_trimesh(vertices: np.ndarray, faces: np.ndarray) -> trimesh.Trimesh:
    """Convert numpy arrays to trimesh object.

    Args:
        vertices: Nx3 array of vertex coordinates
        faces: Mx3 array of face indices

    Returns:
        Trimesh object
    """
    return trimesh.Trimesh(vertices=vertices, faces=faces)


def save_mesh_debug_view(
    mesh: trimesh.Trimesh, output_path: Path | str, view_angle: tuple[float, float] = (45, 45)
) -> None:
    """Save a debug view of the mesh as an image.

    Args:
        mesh: The trimesh object to visualize
        output_path: Path to save the image
        view_angle: Tuple of (azimuth, elevation) angles in degrees
    """
    try:
        # Create a scene with the mesh
        scene = trimesh.Scene(mesh)

        # Save the image with default camera angle
        # Trimesh will automatically position the camera to view the entire mesh
        png = scene.save_image(resolution=[1024, 768])
        with open(output_path, "wb") as f:
            f.write(png)
            print(f"Saved debug view to {output_path}")
    except Exception as e:
        print(f"Could not save debug view: {e}")


def check_mesh_from_stl(stl_path: Path | str, verbose: bool = True) -> dict[str, Any]:
    """Load and validate an STL file.

    Args:
        stl_path: Path to the STL file
        verbose: If True, print diagnostics

    Returns:
        Validation results dictionary
    """
    mesh = trimesh.load(stl_path)
    if isinstance(mesh, trimesh.Scene):
        # If it's a scene, get the first mesh
        mesh = list(mesh.geometry.values())[0]

    return validate_mesh(mesh, verbose)  # type: ignore[arg-type]
