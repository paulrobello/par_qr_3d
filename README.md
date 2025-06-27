# Par QR 3D

## Description

CLI tool to generate 3D printable STL files from QR codes. Create QR codes with various data types (URLs, WiFi credentials, contact info, etc.) and convert them into 3D models suitable for 3D printing. The generated STL files can be customized with different sizes, heights, and error correction levels.

## Features

- **Multiple QR Code Types**: Generate QR codes for text, URLs, emails, phone numbers, SMS, WiFi credentials, and contact cards
- **3D Model Generation**: Convert QR codes into 3D printable STL files with customizable dimensions
- **Configurable Parameters**: Adjust QR code size, error correction level, base dimensions, and QR pattern depth
- **Text Labels**: Add custom text labels to QR codes with configurable positioning (top/bottom)
- **Terminal Display**: View QR codes directly in your terminal using rich-pixels
- **Border Cropping**: Automatically crop white borders from QR codes (default: 2 pixels)
- **Inverted Mode**: Create inverted QR codes with recessed black areas
- **PNG Export**: Optionally save QR codes as PNG images alongside STL files
- **Rich Terminal UI**: Beautiful output with progress indicators and formatted results
- **Type Safety**: Full type annotations throughout the codebase
- **Modern Python**: Built with modern tooling including uv, ruff, and pyright

## Technology Stack
- **Python 3.11+** - Modern Python with latest features
- **Typer** - Modern CLI framework with Rich integration
- **Rich** - Beautiful terminal output and formatting
- **rich-pixels** - Terminal-based image display
- **qrcode** - QR code generation with PIL support
- **numpy-stl** - STL file creation and manipulation
- **Pillow** - Image processing for QR codes
- **uv** - Fast Python package management

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) for package management (recommended) or pip

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/paulrobello/par_qr_3d.git
cd par_qr_3d

# Install dependencies
uv sync
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/paulrobello/par_qr_3d.git
cd par_qr_3d

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

## Usage

### Basic Usage

Generate a simple text QR code:

```bash
par_qr_3d qr "Hello, World!"
```

This creates:
- `qr_code.png` - The QR code image (200x200 pixels)
- `qr_code.stl` - The 3D model file (50x50x3mm)

### Specifying Output Files

```bash
par_qr_3d qr "Your text here" --output my_qr_code
# Creates my_qr_code.png and my_qr_code.stl
```

### QR Code Types

#### URL QR Code
```bash
par_qr_3d qr "example.com" --type url
# Automatically adds https:// if no protocol specified
```

#### WiFi QR Code
```bash
par_qr_3d qr "MyNetwork" --type wifi --wifi-password "secretpass" --wifi-security WPA
```

#### Email QR Code
```bash
par_qr_3d qr "user@example.com" --type email --email-subject "Hello" --email-body "Message body"
```

#### Phone Number QR Code
```bash
par_qr_3d qr "+1234567890" --type phone
```

#### SMS QR Code
```bash
par_qr_3d qr "+1234567890" --type sms --sms-message "Hello!"
```

#### Contact Card (vCard) QR Code
```bash
par_qr_3d qr "John Doe" --type contact \
  --contact-phone "+1234567890" \
  --contact-email "john@example.com" \
  --contact-org "ACME Corp"
```

### Customizing Dimensions

#### QR Code Size and Error Correction
```bash
# Larger QR code with high error correction
par_qr_3d qr "Important data" --size 400 --error-correction H

# Available error correction levels:
# L - Low (7% error correction)
# M - Medium (15% error correction)  
# Q - Quartile (25% error correction)
# H - High (30% error correction)
```

#### STL Model Dimensions
```bash
# Custom base size and depths
par_qr_3d qr "Custom model" \
  --base-width 100 \      # Base width in mm (default: 50)
  --base-height 100 \     # Base height in mm (default: 50)  
  --base-thickness 3 \    # Base layer thickness in mm (default: 2)
  --qr-depth 10          # QR pattern depth in mm (default: 1)
```

### Advanced Options

#### Text Labels
Add a text label to your QR code for easy identification:
```bash
# Add label at top (default position)
par_qr_3d qr "https://example.com" --label "Example Website"

# Add label at bottom
par_qr_3d qr "WiFi: guest123" --label "Guest Network" --label-position bottom

# Short options
par_qr_3d qr "Contact info" -l "John Doe" -L bottom
```

Labels are rendered in Roboto Black font suitable for 3D printing with a 2-pixel margin from the QR code. The text is binarized to ensure clean 3D printing without antialiasing artifacts.

You can control the binarization threshold:
```bash
# Lower threshold (more black pixels)
par_qr_3d qr "Data" --label "My Label" --label-threshold 64

# Higher threshold (more white pixels)  
par_qr_3d qr "Data" --label "My Label" --label-threshold 192

# Default threshold is 128
par_qr_3d qr "Data" --label "My Label" -k 128
```

#### Border Cropping
Crop white border from QR code before converting to STL (default: 15 pixels):
```bash
# Use default 15 pixel crop
par_qr_3d qr "Cropped QR"

# Custom crop amount
par_qr_3d qr "Custom crop" --border-crop 4

# Disable cropping
par_qr_3d qr "No crop" --border-crop 0
```

#### Inverted QR Code
Create an inverted QR code where black areas are recessed and white areas are raised:
```bash
par_qr_3d qr "Inverted" --invert
```

#### Display in Terminal
Show the QR code directly in the terminal:
```bash
par_qr_3d qr "Display test" --display
# Or use short option
par_qr_3d qr "Display test" -T
```

#### Skip PNG Generation
Only generate the STL file:
```bash
par_qr_3d qr "STL only" --no-save-png
```

#### Debug Mode
Enable verbose output for troubleshooting:
```bash
par_qr_3d qr "Debug test" --debug
```

### Examples

#### Business Card QR Code
```bash
par_qr_3d qr "Jane Smith" \
  --type contact \
  --contact-phone "+1-555-0123" \
  --contact-email "jane.smith@company.com" \
  --contact-org "Tech Innovations Inc" \
  --output business_card \
  --size 300 \
  --base-width 85.6 \
  --base-height 53.98 \
  --qr-depth 4
```

#### WiFi Guest Network Sign
```bash
par_qr_3d qr "GuestNetwork" \
  --type wifi \
  --wifi-password "welcome2024" \
  --wifi-security WPA \
  --label "Guest WiFi" \
  --output guest_wifi \
  --size 400 \
  --error-correction H \
  --base-width 120 \
  --base-height 120 \
  --qr-depth 8
```

#### Product URL Tag
```bash
par_qr_3d qr "https://shop.example.com/product/12345" \
  --type url \
  --output product_tag \
  --size 200 \
  --base-width 50 \
  --base-height 50 \
  --base-thickness 1.5 \
  --qr-depth 3
```

## Output Files

The tool generates two files by default:

1. **PNG Image** (`*.png`): The QR code as a standard image file for preview and testing
2. **STL File** (`*.stl`): The 3D model ready for slicing and 3D printing

The STL model includes:
- A solid base plate covering the entire area
- Black QR code modules extruded upward from the base plate
- White areas remain at base height
- Properly closed mesh suitable for 3D printing

## 3D Printing Tips

1. **Print Settings**:
   - Layer height: 0.2mm or finer for better QR code definition
   - Infill: 20-30% is usually sufficient
   - No supports needed for standard models

2. **Size Considerations**:
   - Ensure the printed size is large enough for QR code scanning
   - Minimum recommended size: 30x30mm for simple QR codes
   - Larger sizes needed for complex data or high error correction

3. **Contrast**:
   - Use contrasting filament colors (black on white, white on black)
   - Consider painting the raised portions for better scanning

## CLI Options Reference

### Required Arguments
- `DATA` - The data to encode in the QR code

### Optional Arguments

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output file path (without extension) | `qr_code` |
| `--type` | `-t` | QR code type: text, url, email, phone, sms, wifi, contact | `text` |
| `--size` | `-s` | QR code size in pixels (100-1000) | `200` |
| `--error-correction` | `-e` | Error correction level: L, M, Q, H | `L` |
| `--base-width` | `-w` | STL base width in mm (10-500) | `50.0` |
| `--base-height` | `-h` | STL base height in mm (10-500) | `50.0` |
| `--base-thickness` | `-b` | Base plate thickness in mm (0.5-20) | `2.0` |
| `--qr-depth` | `-d` | QR pattern depth in mm (0.5-20) | `1.0` |
| `--invert` | `-i` | Invert QR code (black recessed) | `False` |
| `--border-crop` | `-c` | Pixels to crop from border (0-20) | `15` |
| `--label` | `-l` | Add text label to QR code | `None` |
| `--label-position` | `-L` | Label position: top or bottom | `top` |
| `--label-threshold` | `-k` | Threshold for label text binarization (0-255) | `128` |
| `--save-png/--no-save-png` | `-p/-P` | Save PNG image | `True` |
| `--display` | `-T` | Display QR code in terminal | `False` |
| `--debug` | `-D` | Enable debug output | `False` |

### Type-Specific Options

#### WiFi Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--wifi-password` | `-W` | WiFi password | `None` |
| `--wifi-security` | `-S` | Security type: WPA, WEP, nopass | `WPA` |

#### Email Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--email-subject` | `-E` | Email subject | `None` |
| `--email-body` | `-B` | Email body | `None` |

#### SMS Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--sms-message` | `-M` | SMS message text | `None` |

#### Contact (vCard) Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--contact-phone` | `-P` | Contact phone number | `None` |
| `--contact-email` | `-C` | Contact email address | `None` |
| `--contact-org` | `-O` | Contact organization | `None` |

## Development

### Running from Source
```bash
uv run par_qr_3d qr "Development test"
```

### Code Quality
```bash
# Format, lint, and type check
make checkall

# Individual commands
make format     # Format with ruff
make lint       # Lint with ruff
make typecheck  # Type check with pyright
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Paul Robello - probello@gmail.com
