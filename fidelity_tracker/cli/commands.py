"""
CLI commands using Click
Main entry point for the application
"""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger
from datetime import datetime
from pathlib import Path

from fidelity_tracker.core.collector import PortfolioCollector
from fidelity_tracker.core.enricher import DataEnricher
from fidelity_tracker.core.database import DatabaseManager
from fidelity_tracker.core.storage import StorageManager
from fidelity_tracker.utils.config import Config
from fidelity_tracker.utils.logger import setup_logging

console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Fidelity Portfolio Tracker - Automated portfolio data collection and analysis"""
    ctx.ensure_object(dict)

    # Load configuration
    ctx.obj['config'] = Config(config) if config else Config()

    # Setup logging
    log_level = 'DEBUG' if verbose else ctx.obj['config'].get('logging.level', 'INFO')
    setup_logging(
        level=log_level,
        log_file=ctx.obj['config'].get('logging.file', 'logs/portfolio-tracker.log'),
        rotation=ctx.obj['config'].get('logging.rotation', '10 MB'),
        retention=ctx.obj['config'].get('logging.retention', '30 days')
    )


@cli.command()
@click.pass_context
def setup(ctx):
    """Interactive setup wizard"""
    console.print("\n[bold blue]Fidelity Portfolio Tracker - Setup Wizard[/bold blue]\n")

    config = ctx.obj['config']

    # Get Fidelity credentials
    console.print("[yellow]Step 1: Fidelity Credentials[/yellow]")
    username = click.prompt("Fidelity Username", type=str)
    password = click.prompt("Fidelity Password", type=str, hide_input=True)
    mfa_secret = click.prompt("Fidelity MFA Secret (TOTP key)", type=str)

    # Update config
    config.set('credentials.fidelity.username', username)
    config.set('credentials.fidelity.password', password)
    config.set('credentials.fidelity.mfa_secret', mfa_secret)

    # Sync settings
    console.print("\n[yellow]Step 2: Sync Settings[/yellow]")
    if click.confirm("Enable automatic daily sync?", default=True):
        schedule = click.prompt("Cron schedule", default="0 18 * * *")
        config.set('sync.schedule', schedule)

    # Enrichment settings
    console.print("\n[yellow]Step 3: Enrichment Settings[/yellow]")
    enable_enrichment = click.confirm("Enable Yahoo Finance enrichment?", default=True)
    config.set('enrichment.enabled', enable_enrichment)

    if enable_enrichment:
        delay = click.prompt("API delay (seconds)", type=float, default=3.0)
        config.set('enrichment.delay_seconds', delay)

    # Storage settings
    console.print("\n[yellow]Step 4: Storage Settings[/yellow]")
    retention_days = click.prompt("Data retention (days)", type=int, default=90)
    config.set('storage.retention_days', retention_days)

    # Save configuration
    config.save()
    console.print("\n[green]✓ Configuration saved![/green]")

    # Test connection
    if click.confirm("\nTest Fidelity connection?", default=True):
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("Testing connection...", total=None)

                collector = PortfolioCollector(**config.get_credentials())
                collector.connect()
                collector.disconnect()

            console.print("[green]✓ Connection successful![/green]")
        except Exception as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            return

    # Initialize database
    if click.confirm("\nInitialize database?", default=True):
        db_path = config.get('database.path', 'fidelity_portfolio.db')
        DatabaseManager(db_path)
        console.print(f"[green]✓ Database initialized at {db_path}[/green]")

    # Run first sync
    if click.confirm("\nRun first data sync?", default=True):
        ctx.invoke(sync)

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("Run [bold]portfolio-tracker --help[/bold] to see available commands")


@cli.command()
@click.option('--enrich/--no-enrich', default=None, help='Enable/disable enrichment')
@click.pass_context
def sync(ctx, enrich):
    """Pull data from Fidelity"""
    config = ctx.obj['config']

    console.print("[bold blue]Syncing portfolio data...[/bold blue]\n")

    try:
        # Collect data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Connecting to Fidelity...", total=None)

            collector = PortfolioCollector(**config.get_credentials())
            data = collector.run()

            progress.update(task, description="Data collected ✓")

        # Enrichment
        should_enrich = enrich if enrich is not None else config.get('enrichment.enabled', True)

        if should_enrich:
            console.print("\n[yellow]Enriching data with Yahoo Finance...[/yellow]")
            enricher = DataEnricher(
                delay=config.get('enrichment.delay_seconds', 3.0),
                max_retries=config.get('enrichment.max_retries', 3)
            )
            data = enricher.enrich_data(data)

        # Save data
        console.print("\n[yellow]Saving data...[/yellow]")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save to storage
        storage = StorageManager(config.get('storage.output_dir', '.'))
        files = storage.save_all(data, timestamp)

        console.print(f"  ✓ JSON: {files['json']}")
        console.print(f"  ✓ Accounts CSV: {files['accounts_csv']}")
        console.print(f"  ✓ Holdings CSV: {files['holdings_csv']}")

        # Save to database
        db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))
        snapshot_id = db.save_snapshot(data)
        console.print(f"  ✓ Database (snapshot #{snapshot_id})")

        # Summary
        total_value = sum(acc.get('balance', 0) for acc in data['accounts'].values())
        num_accounts = len(data['accounts'])

        console.print(f"\n[bold green]✓ Sync complete![/bold green]")
        console.print(f"  Total Accounts: {num_accounts}")
        console.print(f"  Total Value: ${total_value:,.2f}")

    except Exception as e:
        logger.exception("Sync failed")
        console.print(f"\n[bold red]✗ Sync failed: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument('json_file', type=click.Path(exists=True), required=False)
@click.pass_context
def enrich(ctx, json_file):
    """Enrich existing data with Yahoo Finance"""
    config = ctx.obj['config']

    # Find latest JSON file if not specified
    if not json_file:
        storage = StorageManager(config.get('storage.output_dir', '.'))
        json_files = storage.list_snapshots('json')
        if not json_files:
            console.print("[red]No data files found. Run 'portfolio-tracker sync' first.[/red]")
            return
        json_file = json_files[0]
        console.print(f"Using latest file: {json_file}")

    import json
    with open(json_file) as f:
        data = json.load(f)

    console.print("\n[bold blue]Enriching data...[/bold blue]\n")

    enricher = DataEnricher(
        delay=config.get('enrichment.delay_seconds', 3.0),
        max_retries=config.get('enrichment.max_retries', 3)
    )
    data = enricher.enrich_data(data)

    # Save enriched data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    storage = StorageManager(config.get('storage.output_dir', '.'))
    files = storage.save_all(data, f"enriched_{timestamp}")

    console.print(f"\n[green]✓ Enrichment complete![/green]")
    console.print(f"  Saved to: {files['json']}")


@cli.command()
@click.option('--limit', '-n', default=10, help='Number of snapshots to show')
@click.pass_context
def status(ctx, limit):
    """Show portfolio status and recent snapshots"""
    config = ctx.obj['config']
    db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))

    # Get latest snapshot
    latest = db.get_latest_snapshot()
    if not latest:
        console.print("[yellow]No data available. Run 'portfolio-tracker sync' first.[/yellow]")
        return

    console.print(f"\n[bold]Latest Snapshot[/bold]")
    console.print(f"  Timestamp: {latest['timestamp']}")
    console.print(f"  Total Value: ${latest['total_value']:,.2f}")

    # Show recent snapshots
    snapshots = db.get_snapshots(limit)

    table = Table(title=f"\nRecent Snapshots (last {len(snapshots)})")
    table.add_column("ID", justify="right")
    table.add_column("Timestamp")
    table.add_column("Total Value", justify="right")

    for snap in snapshots:
        table.add_row(
            str(snap['id']),
            snap['timestamp'],
            f"${snap['total_value']:,.2f}"
        )

    console.print(table)


@cli.command()
@click.option('--days', '-d', default=90, help='Keep snapshots from last N days')
@click.option('--files/--no-files', default=True, help='Clean up old data files')
@click.option('--database/--no-database', default=True, help='Clean up old database snapshots')
@click.pass_context
def cleanup(ctx, days, files, database):
    """Clean up old data files and database snapshots"""
    config = ctx.obj['config']

    if files:
        storage = StorageManager(config.get('storage.output_dir', '.'))
        deleted = storage.cleanup_old_files(days)
        console.print(f"[green]✓ Deleted {deleted} old data files[/green]")

    if database:
        db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))
        deleted = db.cleanup_old_snapshots(days)
        console.print(f"[green]✓ Deleted {deleted} old database snapshots[/green]")
        db.vacuum()
        console.print("[green]✓ Database optimized[/green]")


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Launch web dashboard"""
    console.print("[bold blue]Launching web dashboard...[/bold blue]")
    console.print("Dashboard will open in your browser at http://localhost:8501")

    import subprocess
    subprocess.run(['streamlit', 'run', 'web/app.py'])


if __name__ == '__main__':
    cli(obj={})
