__version__ = "1.0.0"

from importlib import resources


def get_path() -> str:
    """Directory containing the compiled .dawg dictionaries."""
    return str(resources.files(__name__) / "data")
