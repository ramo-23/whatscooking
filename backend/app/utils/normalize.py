import re

def normalize_ingredient_name(name: str) -> str:
    """
    Normalizes ingredient_names for consistent database storage and matching.
    - Strips leading/training whitespace
    - Converts to lowercase
    - Replaces multiple consecutive spaces with a single space
    """
    name = name.strip().lower()
    name = re.sub(r'\s+', ' ', name)
    return name