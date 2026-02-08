"""
ISORA - Configuration Settings

Central configuration for the ISORA application.
All settings can be overridden via environment variables.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import os


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EXPORTS_DIR = PROJECT_ROOT / "exports"
PLAYBOOKS_DIR = DATA_DIR / "playbooks"
SCENARIOS_DIR = DATA_DIR / "scenarios"
TEMPLATES_DIR = DATA_DIR / "templates"


@dataclass
class DatabaseConfig:
    """SQLite database configuration."""
    db_path: Path = field(default_factory=lambda: DATA_DIR / "cyberops_companion.db")
    echo: bool = False  # SQL logging


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_file: Optional[Path] = None


@dataclass
class UIConfig:
    """Streamlit UI configuration."""
    page_title: str = "ISORA"
    page_icon: str = "🛡️"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    theme: str = "light"  # "light" or "dark"
    theme_primary_color: str = "#1f77b4"
    theme_background_color: str = "#0e1117"
    theme_secondary_background: str = "#262730"
    theme_text_color: str = "#fafafa"


@dataclass
class ForensicsConfig:
    """Forensic integrity settings."""
    hash_algorithm: str = "sha256"
    enable_hash_chain: bool = True
    timestamp_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    timezone: str = "UTC"


@dataclass
class SimulationConfig:
    """Simulation mode settings."""
    enabled: bool = True
    simulation_marker: str = "[CYBEROPS_COMPANION_SIMULATION]"
    default_scenario: str = "corporate_workstation"
    auto_cleanup: bool = True
    vm_connection_timeout: int = 30


@dataclass
class ExportConfig:
    """Report export settings."""
    default_format: str = "markdown"
    include_hashes: bool = True
    include_timestamps: bool = True
    company_name: str = "Organization Name"
    report_author: str = "Security Analyst"


@dataclass
class AppConfig:
    """Main application configuration."""
    app_name: str = "ISORA"
    version: str = "2.0.0"
    debug: bool = False

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    forensics: ForensicsConfig = field(default_factory=ForensicsConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    def __post_init__(self) -> None:
        """Load environment variable overrides."""
        self.debug = os.getenv("CYBEROPS_COMPANION_DEBUG", "").lower() == "true"

        if log_level := os.getenv("CYBEROPS_COMPANION_LOG_LEVEL"):
            self.logging.level = log_level

        if db_path := os.getenv("CYBEROPS_COMPANION_DB_PATH"):
            self.database.db_path = Path(db_path)


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    directories = [
        DATA_DIR,
        EXPORTS_DIR,
        PLAYBOOKS_DIR,
        SCENARIOS_DIR,
        TEMPLATES_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
