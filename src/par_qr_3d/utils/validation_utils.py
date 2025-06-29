"""Input validation utilities."""

from __future__ import annotations

import typer
from rich.console import Console

from ..logging_config import get_logger

logger = get_logger(__name__)
console = Console(stderr=True)


def validate_choice(
    value: str,
    choices: list[str],
    parameter_name: str,
    case_sensitive: bool = False,
) -> str:
    """Validate that a value is one of the allowed choices.

    Args:
        value: User input value
        choices: List of valid choices
        parameter_name: Name of the parameter for error messages
        case_sensitive: Whether to perform case-sensitive comparison

    Returns:
        The validated value (potentially normalized to lowercase)

    Raises:
        typer.Exit: If validation fails
    """
    # Normalize for comparison if not case sensitive
    test_value = value if case_sensitive else value.lower()
    test_choices = choices if case_sensitive else [c.lower() for c in choices]

    if test_value not in test_choices:
        console.print(
            f"[bold red]Error:[/bold red] Invalid {parameter_name} '{value}'. Must be one of: {', '.join(choices)}"
        )
        raise typer.Exit(code=1)

    return test_value if not case_sensitive else value


def validate_conflict(
    param1_name: str,
    param1_value: any,  # type: ignore[valid-type]
    param2_name: str,
    param2_value: any,  # type: ignore[valid-type]
    message: str | None = None,
) -> None:
    """Validate that two parameters are not both set.

    Args:
        param1_name: Name of first parameter
        param1_value: Value of first parameter
        param2_name: Name of second parameter
        param2_value: Value of second parameter
        message: Custom error message

    Raises:
        typer.Exit: If both parameters are set
    """
    if param1_value and param2_value:
        error_msg = message or f"Cannot use both {param1_name} and {param2_name} at the same time."
        console.print(f"[bold red]Error:[/bold red] {error_msg}")
        raise typer.Exit(code=1)
