#!/usr/bin/env python3
"""Command-line utility to check STL files for geometry issues."""

import sys
from pathlib import Path

from .utils import check_mesh_from_stl


def main() -> None:
    """Check an STL file for geometry issues."""
    if len(sys.argv) != 2:
        print("Usage: python -m par_qr_3d.check_stl <stl_file>")
        sys.exit(1)

    stl_path = Path(sys.argv[1])
    if not stl_path.exists():
        print(f"Error: File '{stl_path}' not found")
        sys.exit(1)

    print(f"\nChecking STL file: {stl_path}")
    print("-" * 50)

    results = check_mesh_from_stl(stl_path, verbose=True)

    # Print summary
    print("\n" + "=" * 50)
    if results["is_watertight"] and results["duplicate_faces"] == 0:
        print("✓ Mesh appears to be valid for 3D printing")
    else:
        print("⚠ Mesh has issues that may cause problems in slicing:")
        if not results["is_watertight"]:
            print("  - Mesh is not watertight (has holes)")
        if results["duplicate_faces"] > 0:
            print(f"  - {results['duplicate_faces']} duplicate faces found")
        if results["non_manifold_edges"] > 0:
            print(f"  - {results['non_manifold_edges']} non-manifold edges found")


if __name__ == "__main__":
    main()
