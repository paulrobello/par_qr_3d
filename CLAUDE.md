# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Par QR 3D is a CLI tool that generates 3D printable STL files from QR codes. It allows users to create QR codes with custom data and convert them into 3D models suitable for 3D printing. The project is built with modern Python tooling and follows best practices for type safety and code quality.

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
  - `__main__.py`: CLI entry point using Typer
  - `logging_config.py`: Logging setup with Rich integration

### Entry Points
- CLI script: `par_qr_3d`
- Main app: `par_qr_3d.__main__:app`

### Key Dependencies
- `typer` - Modern CLI framework
- `rich` - Terminal formatting and output
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

The project has a complete implementation for generating 3D printable STL files from QR codes. The `qr` command supports multiple QR code types (text, URL, WiFi, email, phone, SMS, contact cards) with customizable dimensions and error correction levels.

## Known Test Limitations
- The terminal display of QR image does not work in tests but is working. Do not test that feature. If testing is needed, ask the developer.
