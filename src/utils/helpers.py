"""
Helper utilities for CyberOps Companion.
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import uuid
import re


def generate_incident_id(prefix: str = "INC") -> str:
    """
    Generate a unique incident ID.

    Format: PREFIX-YEAR-XXXXXX (e.g., INC-2024-A1B2C3)
    """
    year = datetime.now().year
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{year}-{unique_part}"


def format_timestamp(
    dt: datetime,
    format_type: str = "full"
) -> str:
    """
    Format a datetime for display.

    Args:
        dt: Datetime object (assumed UTC if no timezone)
        format_type: "full", "date", "time", "iso", "log"

    Returns:
        Formatted string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    formats = {
        "full": "%Y-%m-%d %H:%M:%S %Z",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
        "iso": "%Y-%m-%dT%H:%M:%S.%fZ",
        "log": "%H:%M:%S",
        "report": "%Y-%m-%d %H:%M UTC",
    }

    return dt.strftime(formats.get(format_type, formats["full"]))


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Examples:
        45 -> "45 seconds"
        125 -> "2 minutes 5 seconds"
        3665 -> "1 hour 1 minute"
    """
    if seconds < 60:
        return f"{int(seconds)} seconds"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes < 60:
        if remaining_seconds:
            return f"{minutes} minutes {remaining_seconds} seconds"
        return f"{minutes} minutes"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours < 24:
        if remaining_minutes:
            return f"{hours} hours {remaining_minutes} minutes"
        return f"{hours} hours"

    days = hours // 24
    remaining_hours = hours % 24

    if remaining_hours:
        return f"{days} days {remaining_hours} hours"
    return f"{days} days"


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a string for use as a filename.

    Removes or replaces characters that are invalid in filenames.
    """
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[<>:"/\\|?*\s]+', '_', filename)

    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip('_.')

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')

    # Ensure we have something
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def compute_file_hash(
    file_path: Path,
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Compute the hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (sha256, sha1, md5)
        chunk_size: Size of chunks to read

    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def compute_string_hash(content: str, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a string.

    Args:
        content: String to hash
        algorithm: Hash algorithm

    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)
    hash_func.update(content.encode("utf-8"))
    return hash_func.hexdigest()


def truncate_string(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: String to append if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def parse_severity(severity_str: str) -> str:
    """
    Parse and normalize a severity string.

    Args:
        severity_str: Raw severity input

    Returns:
        Normalized severity (critical, high, medium, low, informational)
    """
    normalized = severity_str.lower().strip()

    severity_map = {
        "critical": "critical",
        "crit": "critical",
        "p1": "critical",
        "high": "high",
        "p2": "high",
        "medium": "medium",
        "med": "medium",
        "p3": "medium",
        "low": "low",
        "p4": "low",
        "info": "informational",
        "informational": "informational",
        "p5": "informational",
    }

    return severity_map.get(normalized, "medium")


def get_phase_emoji(phase: str) -> str:
    """Get an emoji for a phase (for display purposes)."""
    emojis = {
        "detection": "🔍",
        "analysis": "🔬",
        "containment": "🛡️",
        "eradication": "🧹",
        "recovery": "🔄",
        "post_incident": "📝",
    }
    return emojis.get(phase.lower(), "📋")


def get_status_color(status: str) -> str:
    """Get a color code for a status (for UI purposes)."""
    colors = {
        "not_started": "#808080",  # Gray
        "in_progress": "#1f77b4",  # Blue
        "completed": "#2ca02c",    # Green
        "skipped": "#ff7f0e",      # Orange
        "draft": "#808080",
        "active": "#1f77b4",
        "contained": "#ff7f0e",
        "eradicated": "#9467bd",   # Purple
        "recovered": "#2ca02c",
        "closed": "#2ca02c",
    }
    return colors.get(status.lower(), "#808080")
