"""CSV field and boolean conversion helpers shared by both CLI implementations."""

def parse_bool(value):
    """Parse unambiguous CSV boolean literals; reject unknown values."""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "y", "on"):
        return True
    if text in ("false", "0", "no", "n", "off", ""):
        return False
    raise ValueError(f"Invalid boolean value {value!r}; expected true or false")


def append_unique_fields(existing, additions):
    """Preserve input header order without duplicate output field names."""
    return list(dict.fromkeys([*existing, *additions]))
