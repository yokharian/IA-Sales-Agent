import unidecode
from typing import Union


def normalize_text(text: Union[str, None]) -> str:
    """
    Normalize text by removing accents, converting to lowercase, and stripping whitespace.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text string
    """
    if text is None:
        return ""

    # Convert to string if not already
    text = str(text)

    # Remove accents and normalize
    normalized = unidecode.unidecode(text)

    # Convert to lowercase and strip whitespace
    return normalized.lower().strip()


def parse_boolean(value: Union[str, int, bool, None]) -> bool:
    """
    Parse various string representations to boolean.

    Args:
        value: Value to parse (string, int, bool, or None)

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    # Convert to string and normalize
    str_value = str(value).lower().strip()

    # Check for truthy values
    truthy_values = ["sí", "si", "yes", "true", "1", "verdadero", "v"]
    return str_value in truthy_values


def safe_int(value: Union[str, int, None], default: int = 0) -> int:
    """
    Safely convert value to integer with default fallback.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    if isinstance(value, int):
        return value

    if value is None:
        return default

    try:
        # Remove any non-numeric characters except minus sign
        cleaned = str(value).strip().replace(",", "").replace(" ", "")
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default


def safe_float(value: Union[str, int, float, None], default: float = 0.0) -> float:
    """
    Safely convert value to float with default fallback.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if isinstance(value, (int, float)):
        return float(value)

    if value is None:
        return default

    try:
        # Remove any non-numeric characters except minus sign and decimal point
        cleaned = str(value).strip().replace(",", "").replace(" ", "")
        return float(cleaned)
    except (ValueError, TypeError):
        return default
