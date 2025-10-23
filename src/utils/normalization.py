from typing import Union


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
