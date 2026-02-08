"""
ISORA CLI Entry Point

Command-line interface for launching the application.
"""

import click
import subprocess
import sys
from pathlib import Path

from config import ensure_directories, get_config, DATA_DIR


@click.group()
@click.version_option(version="0.1.0", prog_name="ISORA")
def cli():
    """ISORA - Incident Response Decision Support Tool"""
    pass


@cli.command()
@click.option("--port", default=8501, help="Port to run the web UI on")
@click.option("--host", default="localhost", help="Host to bind to")
def ui(port: int, host: str):
    """Launch the Streamlit web interface."""
    ensure_directories()

    app_path = Path(__file__).parent / "ui" / "app.py"

    click.echo(f"Starting ISORA on http://{host}:{port}")
    click.echo("Press Ctrl+C to stop")

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(port),
        "--server.address", host,
        "--browser.gatherUsageStats", "false",
    ])


@cli.command()
def init():
    """Initialize the ISORA environment."""
    click.echo("Initializing ISORA...")

    ensure_directories()

    config = get_config()

    click.echo(f"✓ Data directory: {DATA_DIR}")
    click.echo(f"✓ Database: {config.database.db_path}")
    click.echo("✓ Initialization complete")


@cli.command()
@click.argument("incident_id")
def verify(incident_id: str):
    """Verify evidence chain integrity for an incident."""
    from src.core.evidence_logger import EvidenceLogger

    ensure_directories()

    logger = EvidenceLogger()
    is_valid, invalid_idx, message = logger.verify_chain(incident_id)

    if is_valid:
        click.echo(click.style(f"✓ {message}", fg="green"))
    else:
        click.echo(click.style(f"✗ {message}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("incident_id")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
def export(incident_id: str, output: str):
    """Export an incident report."""
    click.echo(f"Exporting incident {incident_id}...")
    click.echo("Note: Full export requires using the web UI for complete data.")


@cli.command()
def scenarios():
    """List available training scenarios."""
    from src.simulation.scenario_runner import ScenarioRunner

    runner = ScenarioRunner()
    scenarios_list = runner.list_scenarios()

    click.echo("\nAvailable Training Scenarios:")
    click.echo("=" * 50)

    for scenario in scenarios_list:
        click.echo(f"\n{scenario['name']}")
        click.echo(f"  ID: {scenario['id']}")
        click.echo(f"  Difficulty: {scenario['difficulty']}")
        click.echo(f"  {scenario['description']}")


@cli.command()
def version():
    """Show version information."""
    config = get_config()
    click.echo(f"ISORA v{config.version}")
    click.echo("Incident Response Decision Support Tool")
    click.echo("\nA product-oriented security tool for IHK Final Project")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
