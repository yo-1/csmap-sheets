"""Filename rules shared by the GUI and Processing execution."""


def json_path(value):
    """Keep existing JSON suffixes (including uppercase), append otherwise."""
    value = str(value).strip()
    if not value or value.lower().endswith(".json"):
        return value
    return value + ".json"
