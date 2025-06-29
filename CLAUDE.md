# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Par QR 3D is a CLI tool that generates 3D printable STL and 3MF files from QR codes. It allows users to create QR codes with custom data and convert them into 3D models suitable for 3D printing. The project supports advanced features like color materials, mounting options, multi-layer heights, and artistic styles. Built with modern Python tooling and follows best practices for type safety and code quality.

## Development Commands

### Core Development Workflow
- `make checkall` - Format code, run linter, and type check (run after any code changes)
- `uv run par_qr_3d --help` - Show available commands
- `uv run par_qr_3d qr "Your QR data"` - Generate QR code from data
- `make run` - Run the application

### Package Management
- `uv sync` - Sync dependencies
- `uv add <package>` - Add new dependencies
- `uv remove <package>` - Remove dependencies
- `make depsupdate` - Update all dependencies
- `make setup` - Initial setup (uv lock + sync)
- `make resetup` - Recreate virtual environment from scratch

### Code Quality Tools
- `make format` - Format code with ruff
- `make lint` - Run ruff linter with fixes
- `make typecheck` - Run pyright type checker
- `make pre-commit` - Run pre-commit hooks

### Profiling
- `make profile` - Profile with scalene
- `make profile2` - Profile with pyinstrument


### Development Guidelines
- **Important:** Run `npm run lint && npm run build` after code changes. You do not need to run lint and build for documentation changes.
- ALWAYS update documentation when making architectural or event related changes
- Use `uv run` for Python scripts


## Project Architecture

### Core Structure
- **src/par_qr_3d/**: Main package directory
  - `__init__.py`: Package metadata and version info
  - `__main__.py`: CLI entry point using Typer with comprehensive QR options
  - `logging_config.py`: Logging setup with Rich integration
  - `qr_generator.py`: QR code generation with various types and styles
  - `stl_converter.py`: 3D model generation with shared geometry functions
  - **utils/**: Shared utility modules
    - `color_utils.py`: Color parsing, RGB normalization, 3MF format conversion
    - `font_utils.py`: Font loading with bundled fonts and emoji detection
    - `image_utils.py`: Image mode conversion utilities
    - `validation_utils.py`: Input validation and conflict checking
    - `path_utils.py`: File path handling and preparation
    - `platform_utils.py`: OS-specific operations (file opening)

### Entry Points
- CLI script: `par_qr_3d`
- Main app: `par_qr_3d.__main__:app`

### Key Dependencies
- `typer` - Modern CLI framework
- `rich` - Terminal formatting and output
- `qrcode` - QR code generation
- `numpy-stl` - STL file creation
- `lib3mf` - 3MF file format support
- `scipy` - Connected component analysis for frame detection
- `Pillow` - Image processing
- `pydantic` - Data validation
- `python-dotenv` - Environment variable management

### Configuration
- **Python**: 3.11+ required
- **ruff**: Line length 120, Google-style docstrings
- **pyright**: Basic type checking, Python 3.12 target
- **Environment**: Loads from `.env` and `~/.par_qr_3d.env`

### Development Standards
- Type annotations required for all functions and methods
- Google-style docstrings
- UTF-8 encoding for file operations
- Uses `uv` for package management
- Follows src/ layout pattern
- Error handling with user-friendly messages via Rich console

## Current Implementation Status

The project has a complete implementation for generating 3D printable files from QR codes:

### Completed Features
- **QR Code Types**: text, URL, WiFi, email, phone, SMS, contact cards (vCard)
- **3D Formats**: STL (monochrome) and 3MF (with color materials)
- **Export Formats**: PNG (raster), SVG (vector)
- **Visual Features**: Custom colors, text labels, center text/emoji (with bundled fonts), image overlays, decorative frames, artistic patterns
- **3D Features**: Multi-layer heights, mounting options (keychain loops), inverted mode
- **UI Features**: Auto-open generated files, terminal QR display, rich progress output
- **Advanced**: Frame detection using connected component analysis, shared geometry generation for consistency

### Architecture Highlights
- **Shared Utilities**: Centralized utilities eliminate code duplication (~440+ lines saved)
- **Shared Geometry**: Common functions generate vertices/triangles for both STL and 3MF
- **Component Tracking**: Geometry tagged by component type (base, QR, walls) for material assignment
- **Smart Triangulation**: Ring-pattern triangulation for proper hole geometry in keychain mounts
- **Format Optimization**: STL includes walls for printing, 3MF optimized for visual rendering
- **Cross-Platform**: Font loading and file opening work on macOS, Linux, and Windows
- **Bundled Fonts**: Includes NotoEmoji-Regular.ttf for emoji, DejaVuSans.ttf for Unicode, Roboto-Black.ttf for labels
- **Type Safety**: Full type annotations with pyright checking

## Known Test Limitations
- The terminal display of QR image does not work in tests but is working. Do not test that feature. If testing is needed, ask the developer.
