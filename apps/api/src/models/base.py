"""Base utilities for models."""
from uuid import uuid4


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())
