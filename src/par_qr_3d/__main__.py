"""Main application with improved CLI structure and features."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.pretty import Pretty
from rich_pixels import Pixels

from . import __application_binary__, __application_title__, __version__
from .logging_config import get_logger, setup_logging
from .qr_generator import ErrorCorrectionLevel, QRType, add_label_to_qr, crop_qr_border, generate_qr_code, save_qr_code
from .stl_converter import convert_qr_to_stl

# Create the main Typer app with rich help
app = typer.Typer(
    name=__application_binary__,
    help=f"{__application_title__} - A 3D Printable QR Code Generator",
    rich_markup_mode="rich",
    add_completion=False,
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console(stderr=True)
logger = get_logger(__name__)

# Load environment variables
load_dotenv()
load_dotenv(Path(f"~/.{__application_binary__}.env").expanduser())


def version_callback(value: bool) -> None:
    """Print version and exit.

    Args:
        value: If True, print version and exit.

    Raises:
        typer.Exit: Always raised when value is True.
    """
    if value:
        console.print(f"[bold blue]{__application_title__}[/bold blue] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Par QR 3D - A 3D Printable QR Code Generator.

    Args:
        version: Version flag. If provided, prints version and exits.
    """
    pass


@app.command("qr", help="Generate a 3D printable STL file from QR code data")
def qr_command(
    data: Annotated[
        str,
        typer.Argument(
            help="Data to encode in the QR code",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (without extension). Defaults to 'qr_code'",
        ),
    ] = None,
    qr_type: Annotated[
        QRType,
        typer.Option(
            "--type",
            "-t",
            help="Type of QR code to generate",
        ),
    ] = QRType.TEXT,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            "-s",
            help="Size of the QR code in pixels",
            min=100,
            max=1000,
        ),
    ] = 200,
    error_correction: Annotated[
        ErrorCorrectionLevel,
        typer.Option(
            "--error-correction",
            "-e",
            help="Error correction level",
        ),
    ] = ErrorCorrectionLevel.LOW,
    base_width: Annotated[
        float,
        typer.Option(
            "--base-width",
            "-w",
            help="Width of the STL base in mm",
            min=10.0,
            max=500.0,
        ),
    ] = 50.0,
    base_height: Annotated[
        float,
        typer.Option(
            "--base-height",
            "-h",
            help="Height of the STL base in mm",
            min=10.0,
            max=500.0,
        ),
    ] = 50.0,
    base_thickness: Annotated[
        float,
        typer.Option(
            "--base-thickness",
            "-b",
            help="Thickness of the solid base plate in mm",
            min=0.5,
            max=20.0,
        ),
    ] = 2.0,
    qr_depth: Annotated[
        float,
        typer.Option(
            "--qr-depth",
            "-d",
            help="Height of QR code black modules above base in mm",
            min=0.5,
            max=20.0,
        ),
    ] = 1.0,
    invert: Annotated[
        bool,
        typer.Option(
            "--invert",
            "-i",
            help="Invert the QR code (black recessed, white raised)",
        ),
    ] = False,
    border_crop: Annotated[
        int,
        typer.Option(
            "--border-crop",
            "-c",
            help="Pixels to crop from QR code border (0 to disable)",
            min=0,
            max=20,
        ),
    ] = 15,
    save_png: Annotated[
        bool,
        typer.Option(
            "--save-png/--no-save-png",
            "-p/-P",
            help="Save the QR code as a PNG image",
        ),
    ] = True,
    display: Annotated[
        bool,
        typer.Option(
            "--display",
            "-T",
            help="Display the QR code in the terminal",
        ),
    ] = False,
    label: Annotated[
        str | None,
        typer.Option(
            "--label",
            "-l",
            help="Add a text label to the QR code",
        ),
    ] = None,
    label_position: Annotated[
        str,
        typer.Option(
            "--label-position",
            "-L",
            help="Label position: top or bottom",
        ),
    ] = "top",
    label_threshold: Annotated[
        int,
        typer.Option(
            "--label-threshold",
            "-k",
            help="Threshold for label text binarization (0-255)",
            min=0,
            max=255,
        ),
    ] = 128,
    overlay_image: Annotated[
        Path | None,
        typer.Option(
            "--overlay-image",
            "-I",
            help="Path to image to overlay in center of QR code",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    overlay_size_percent: Annotated[
        int,
        typer.Option(
            "--overlay-size",
            "-Z",
            help="Size of overlay image as percentage of QR code (10-30)",
            min=10,
            max=30,
        ),
    ] = 20,
    base_color: Annotated[
        str,
        typer.Option(
            "--base-color",
            "-bc",
            help="Base/background color (name or hex code)",
        ),
    ] = "white",
    qr_color: Annotated[
        str,
        typer.Option(
            "--qr-color",
            "-qc",
            help="QR code module color (name or hex code)",
        ),
    ] = "black",
    no_stl: Annotated[
        bool,
        typer.Option(
            "--no-stl",
            "-N",
            help="Skip STL generation (only create PNG)",
        ),
    ] = False,
    wifi_password: Annotated[
        str | None,
        typer.Option(
            "--wifi-password",
            "-W",
            help="WiFi password (for WiFi QR codes)",
        ),
    ] = None,
    wifi_security: Annotated[
        str,
        typer.Option(
            "--wifi-security",
            "-S",
            help="WiFi security type: WPA, WEP, or nopass (for WiFi QR codes)",
        ),
    ] = "WPA",
    email_subject: Annotated[
        str | None,
        typer.Option(
            "--email-subject",
            "-E",
            help="Email subject (for email QR codes)",
        ),
    ] = None,
    email_body: Annotated[
        str | None,
        typer.Option(
            "--email-body",
            "-B",
            help="Email body (for email QR codes)",
        ),
    ] = None,
    sms_message: Annotated[
        str | None,
        typer.Option(
            "--sms-message",
            "-M",
            help="SMS message (for SMS QR codes)",
        ),
    ] = None,
    contact_phone: Annotated[
        str | None,
        typer.Option(
            "--contact-phone",
            "-P",
            help="Contact phone number (for contact QR codes)",
        ),
    ] = None,
    contact_email: Annotated[
        str | None,
        typer.Option(
            "--contact-email",
            "-C",
            help="Contact email (for contact QR codes)",
        ),
    ] = None,
    contact_org: Annotated[
        str | None,
        typer.Option(
            "--contact-org",
            "-O",
            help="Contact organization (for contact QR codes)",
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            "-D",
            help="Enable debug mode with verbose output",
        ),
    ] = False,
) -> None:
    """Generate a 3D printable STL file from QR code data.

    This is the main command that creates QR codes and converts them to 3D printable
    STL files. It supports various QR code types (text, URL, WiFi, email, etc.) and
    provides extensive customization options for the 3D model.

    Args:
        data: The data to encode in the QR code.
        output: Output file path (without extension). Defaults to 'qr_code'.
        qr_type: Type of QR code to generate (text, url, email, phone, sms, wifi, contact).
        size: Size of the QR code in pixels (100-1000).
        error_correction: Error correction level (L=Low, M=Medium, Q=Quartile, H=High).
        base_width: Width of the STL base in mm (10-500).
        base_height: Height of the STL base in mm (10-500).
        base_thickness: Thickness of the solid base plate in mm (0.5-20).
        qr_depth: Height of QR code black modules above base in mm (0.5-20).
        invert: If True, black areas are recessed and white areas are raised.
        border_crop: Pixels to crop from QR code border (0 to disable).
        save_png: If True, also save the QR code as a PNG image.
        display: If True, display the QR code in the terminal.
        label: Optional text label to add to the QR code.
        label_position: Position of the label (top or bottom).
        label_threshold: Threshold value for label text binarization (0-255).
        overlay_image: Path to an image file to overlay in the center of the QR code.
        overlay_size_percent: Size of the overlay as a percentage of QR code size (10-30%).
        base_color: Background color of the QR code (name or hex code).
        qr_color: Color of the QR code modules (name or hex code).
        no_stl: If True, skip STL generation and only create PNG.
        wifi_password: WiFi password (for WiFi QR codes).
        wifi_security: WiFi security type (WPA, WEP, or nopass).
        email_subject: Email subject (for email QR codes).
        email_body: Email body (for email QR codes).
        sms_message: SMS message text (for SMS QR codes).
        contact_phone: Contact phone number (for contact QR codes).
        contact_email: Contact email address (for contact QR codes).
        contact_org: Contact organization (for contact QR codes).
        debug: If True, enable debug mode with verbose output.

    Raises:
        typer.Exit: On user cancellation (code 0) or error (code 1).

    Note:
        The function creates two files by default:
        - A PNG image file for preview (unless --no-save-png is used)
        - An STL file for 3D printing
    """
    try:
        # Setup logging
        setup_logging(debug=debug)
        logger.debug("Starting qr command")

        # Set default output path
        if output is None:
            output = Path("qr_code")

        # Prepare format kwargs based on QR type
        format_kwargs = {}
        if qr_type == QRType.WIFI:
            if wifi_password:
                format_kwargs["password"] = wifi_password
            format_kwargs["security"] = wifi_security
        elif qr_type == QRType.EMAIL:
            if email_subject:
                format_kwargs["subject"] = email_subject
            if email_body:
                format_kwargs["body"] = email_body
        elif qr_type == QRType.SMS:
            if sms_message:
                format_kwargs["message"] = sms_message
        elif qr_type == QRType.CONTACT:
            if contact_phone:
                format_kwargs["phone"] = contact_phone
            if contact_email:
                format_kwargs["email"] = contact_email
            if contact_org:
                format_kwargs["org"] = contact_org

        # Generate QR code
        console.print("[blue]Generating QR code...[/blue]")
        qr_image = generate_qr_code(
            data=data,
            qr_type=qr_type,
            size=size,
            error_correction=error_correction,
            base_color=base_color,
            qr_color=qr_color,
            **format_kwargs,
        )

        # Crop border if requested
        if border_crop > 0:
            qr_image = crop_qr_border(qr_image, border_crop)
            logger.debug(f"Cropped {border_crop} pixels from QR code border")

        # Add label if requested
        if label:
            # Validate label position
            if label_position.lower() not in ["top", "bottom"]:
                console.print(
                    f"[bold red]Error:[/bold red] Invalid label position '{label_position}'. Must be 'top' or 'bottom'."
                )
                raise typer.Exit(code=1)
            qr_image = add_label_to_qr(qr_image, label, label_position.lower(), threshold=label_threshold)

        # Add overlay image if requested (after label to preserve grayscale)
        if overlay_image:
            from .qr_generator import add_overlay_to_qr

            qr_image = add_overlay_to_qr(qr_image, overlay_image, overlay_size_percent, convert_to_grayscale=not no_stl)
            logger.debug(f"Added overlay image from {overlay_image}")

        # Display in terminal if requested
        if display:
            console.print("\n[bold]QR Code Preview:[/bold]")
            # Get terminal size to calculate appropriate scaling
            term_width = console.width
            term_height = console.height - 10  # Leave room for other output

            # Convert to RGB if needed (rich-pixels may have issues with mode "1" images)
            display_image = qr_image.convert("RGB") if qr_image.mode != "RGB" else qr_image

            # Calculate scale to fit within terminal (each character is roughly 2:1 height:width)
            img_width, img_height = display_image.size

            # Target size that fits in terminal - doubled from previous values
            target_width = min(term_width - 2, 160)  # Leave some margin, doubled from 80
            target_height = min(term_height - 2, 80)  # Doubled from 40

            scale_width = target_width / img_width
            scale_height = target_height / img_height
            scale = min(scale_width, scale_height) * 2.0  # Double the scale

            # Calculate final size
            final_width = int(img_width * scale)
            final_height = int(img_height * scale)

            # Ensure minimum size for QR code visibility - doubled
            min_size = 80  # Doubled from 40
            if final_width < min_size or final_height < min_size:
                final_width = final_height = min_size

            logger.debug(
                f"Terminal size: {term_width}x{term_height}, Image size: {img_width}x{img_height}, "
                f"Final size: {final_width}x{final_height}"
            )

            pixels = Pixels.from_image(display_image, resize=(final_width, final_height))
            console.print(pixels)
            console.print()

        # Save PNG if requested
        if save_png:
            png_path = save_qr_code(qr_image, output.with_suffix(".png"))
            console.print(f"[green]✓[/green] Saved QR code image: {png_path}")

        # Convert to STL if not disabled
        if not no_stl:
            console.print("[blue]Converting to 3D model...[/blue]")
            stl_path = convert_qr_to_stl(
                qr_image=qr_image,
                output_path=output.with_suffix(".stl"),
                base_size_mm=(base_width, base_height),
                base_height_mm=base_thickness,
                qr_height_mm=qr_depth,
                invert=invert,
            )
            console.print(f"[green]✓[/green] Created STL file: {stl_path}")

        # Display summary
        console.print("\n[bold]Summary:[/bold]")
        summary = {
            "QR Type": qr_type.value,
            "QR Size": f"{size}x{size} pixels",
            "Error Correction": error_correction.value,
            "Base Color": base_color,
            "QR Color": qr_color,
            "Border Crop": f"{border_crop} pixels" if border_crop > 0 else "None",
            "Label": f'"{label}" ({label_position})' if label else "None",
        }

        if not no_stl:
            summary.update(
                {
                    "STL Base Size": f"{base_width}x{base_height} mm",
                    "Total Height": f"{base_thickness + qr_depth} mm",
                    "Inverted": "Yes" if invert else "No",
                }
            )
        else:
            summary["STL Generation"] = "Disabled"

        console.print(Pretty(summary))

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        logger.error(f"QR command failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
