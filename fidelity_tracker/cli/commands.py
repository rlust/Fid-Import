"""
CLI commands using Click
Main entry point for the application
"""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger
from datetime import datetime, timedelta
from pathlib import Path

from fidelity_tracker.core.collector import PortfolioCollector
from fidelity_tracker.core.enricher import DataEnricher
from fidelity_tracker.core.database import DatabaseManager
from fidelity_tracker.core.storage import StorageManager
from fidelity_tracker.utils.config import Config
from fidelity_tracker.utils.logger import setup_logging
import fidelity_tracker

console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.version_option(version=fidelity_tracker.__version__, prog_name='portfolio-tracker')
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
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    config = ctx.obj['config']

    console.print("[bold blue]Syncing portfolio data...[/bold blue]\n")

    start_time = datetime.now()

    try:
        # Collect data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Connecting to Fidelity...", total=None)

            try:
                collector = PortfolioCollector(**config.get_credentials())
                data = collector.run()
                progress.update(task, description="✓ Data collected")
            except Exception as e:
                progress.update(task, description="✗ Connection failed")
                console.print(f"\n[red]Error connecting to Fidelity: {e}[/red]")
                console.print("\n[yellow]Troubleshooting tips:[/yellow]")
                console.print("  • Check your credentials in .env file")
                console.print("  • Verify MFA secret is correct (no spaces)")
                console.print("  • Ensure Fidelity website is accessible")
                console.print("  • Check your internet connection")
                raise

        # Enrichment
        should_enrich = enrich if enrich is not None else config.get('enrichment.enabled', True)

        if should_enrich:
            console.print("\n[yellow]Enriching data with Yahoo Finance...[/yellow]")

            # Progress bar for enrichment
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                enrichment_task = progress.add_task("Enriching tickers", total=100)

                def progress_callback(current, total, ticker):
                    progress.update(
                        enrichment_task,
                        completed=current,
                        total=total,
                        description=f"Enriching {ticker}"
                    )

                enricher = DataEnricher(
                    delay=config.get('enrichment.delay_seconds', 3.0),
                    max_retries=config.get('enrichment.max_retries', 3),
                    progress_callback=progress_callback
                )

                try:
                    data = enricher.enrich_data(data)
                    progress.update(enrichment_task, description="✓ Enrichment complete")
                except Exception as e:
                    progress.update(enrichment_task, description="✗ Enrichment failed")
                    console.print(f"\n[yellow]Warning: Enrichment partially failed: {e}[/yellow]")
                    console.print("\n[yellow]Troubleshooting tips:[/yellow]")
                    console.print("  • Rate limited: Wait 1 hour before retrying")
                    console.print(f"  • Increase delay: Set enrichment.delay_seconds > {config.get('enrichment.delay_seconds', 3.0)}")
                    console.print("  • Run enrichment separately: portfolio-tracker enrich")
                    # Continue with unenriched data

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
        elapsed = datetime.now() - start_time
        total_value = sum(acc.get('balance', 0) for acc in data['accounts'].values())
        num_accounts = len(data['accounts'])

        console.print(f"\n[bold green]✓ Sync complete![/bold green]")
        console.print(f"  Total Accounts: {num_accounts}")
        console.print(f"  Total Value: ${total_value:,.2f}")
        console.print(f"  Time Elapsed: {elapsed.total_seconds():.1f}s")

    except Exception as e:
        elapsed = datetime.now() - start_time
        logger.exception("Sync failed")
        console.print(f"\n[bold red]✗ Sync failed after {elapsed.total_seconds():.1f}s[/bold red]")
        console.print(f"  Error: {e}")
        raise click.Abort()


@cli.command()
@click.argument('json_file', type=click.Path(exists=True), required=False)
@click.option('--delay', '-d', type=float, help='Delay between API calls (seconds)')
@click.option('--clear-cache', is_flag=True, help='Clear enrichment cache before starting')
@click.pass_context
def enrich(ctx, json_file, delay, clear_cache):
    """Enrich existing data with Yahoo Finance"""
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
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

    # Use delay from CLI, config, or default
    api_delay = delay if delay is not None else config.get('enrichment.delay_seconds', 3.0)
    console.print(f"Using delay: {api_delay}s between requests")

    # Progress bar for enrichment
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        enrichment_task = progress.add_task("Enriching tickers", total=100)

        def progress_callback(current, total, ticker):
            progress.update(
                enrichment_task,
                completed=current,
                total=total,
                description=f"Enriching {ticker}"
            )

        enricher = DataEnricher(
            delay=api_delay,
            max_retries=config.get('enrichment.max_retries', 3),
            progress_callback=progress_callback
        )

        if clear_cache:
            enricher.clear_cache()
            console.print("[yellow]Cache cleared[/yellow]")

        try:
            data = enricher.enrich_data(data)
            progress.update(enrichment_task, description="✓ Enrichment complete")
        except Exception as e:
            progress.update(enrichment_task, description="✗ Enrichment failed")
            console.print(f"\n[red]Error: {e}[/red]")
            console.print("\n[yellow]Troubleshooting tips:[/yellow]")
            console.print("  • Rate limited: Wait 1 hour and try again")
            console.print("  • Increase delay: Use --delay 5.0 or higher")
            console.print("  • Clear cache: Use --clear-cache flag")
            raise click.Abort()

    # Save enriched data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    storage = StorageManager(config.get('storage.output_dir', '.'))
    files = storage.save_all(data, f"enriched_{timestamp}")

    # Show cache stats
    cache_stats = enricher.get_cache_stats()
    console.print(f"\n[green]✓ Enrichment complete![/green]")
    console.print(f"  Saved to: {files['json']}")
    console.print(f"  Cached tickers: {cache_stats['cached_tickers']}")


@cli.command()
@click.option('--limit', '-n', default=10, help='Number of snapshots to show')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed breakdown')
@click.pass_context
def status(ctx, limit, detailed):
    """Show portfolio status and recent snapshots"""
    config = ctx.obj['config']
    db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))

    # Get latest snapshot
    latest = db.get_latest_snapshot()
    if not latest:
        console.print("[yellow]No data available. Run 'portfolio-tracker sync' first.[/yellow]")
        return

    console.print(f"\n[bold blue]Portfolio Status[/bold blue]\n")
    console.print(f"[bold]Latest Snapshot[/bold]")
    console.print(f"  Timestamp: {latest['timestamp']}")
    console.print(f"  Total Value: ${latest['total_value']:,.2f}")

    if detailed:
        # Get holdings for detailed breakdown
        holdings = db.get_holdings(latest['id'])

        if holdings:
            # Top 5 holdings
            console.print(f"\n[bold]Top 5 Holdings[/bold]")
            for i, holding in enumerate(holdings[:5], 1):
                console.print(
                    f"  {i}. {holding.get('ticker', 'N/A'):6s} "
                    f"${holding.get('value', 0):>12,.2f}  "
                    f"({holding.get('portfolio_weight', 0):>5.2f}%)"
                )

            # Sector breakdown
            if any('sector' in h for h in holdings):
                console.print(f"\n[bold]Sector Allocation[/bold]")
                sectors = {}
                for holding in holdings:
                    sector = holding.get('sector', 'Unknown')
                    if sector not in ['Unknown', 'Cash']:
                        sectors[sector] = sectors.get(sector, 0) + holding.get('value', 0)

                for sector, value in sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (value / latest['total_value']) * 100
                    console.print(f"  {sector:20s} ${value:>12,.2f}  ({percentage:>5.2f}%)")

            # Gain/Loss summary
            if any('gain_loss' in h for h in holdings):
                total_gain_loss = sum(h.get('gain_loss', 0) for h in holdings)
                total_cost = sum(h.get('cost_basis', 0) for h in holdings if h.get('cost_basis'))

                if total_cost > 0:
                    total_return_pct = (total_gain_loss / total_cost) * 100
                    console.print(f"\n[bold]Performance[/bold]")
                    color = "green" if total_gain_loss >= 0 else "red"
                    console.print(f"  Total Gain/Loss: [{color}]${total_gain_loss:,.2f} ({total_return_pct:+.2f}%)[/{color}]")

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
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without deleting')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def cleanup(ctx, days, files, database, dry_run, yes):
    """Clean up old data files and database snapshots"""
    config = ctx.obj['config']

    console.print(f"[bold blue]Cleaning up data older than {days} days...[/bold blue]\n")

    total_to_delete = 0

    if files:
        storage = StorageManager(config.get('storage.output_dir', '.'))

        # Preview files to delete
        from pathlib import Path
        from datetime import datetime, timedelta
        import os

        cutoff_date = datetime.now() - timedelta(days=days)
        files_to_delete = []

        for pattern in ['fidelity_data_*.json', 'fidelity_accounts_*.csv', 'fidelity_holdings_*.csv']:
            for filepath in Path(config.get('storage.output_dir', '.')).glob(pattern):
                if filepath.stat().st_mtime < cutoff_date.timestamp():
                    size = filepath.stat().st_size
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    files_to_delete.append((filepath, size, mtime))

        if files_to_delete:
            console.print("[yellow]Files to delete:[/yellow]")
            total_size = 0
            for filepath, size, mtime in files_to_delete:
                console.print(f"  • {filepath.name} ({size / 1024:.1f} KB, {mtime.strftime('%Y-%m-%d')})")
                total_size += size
            console.print(f"  Total: {len(files_to_delete)} files, {total_size / 1024 / 1024:.2f} MB\n")
            total_to_delete += len(files_to_delete)
        else:
            console.print("[green]No old files to delete[/green]\n")

    if database:
        db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        # Preview snapshots to delete
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, timestamp, total_value FROM snapshots WHERE timestamp < ? ORDER BY timestamp DESC',
            (cutoff_date.isoformat(),)
        )
        snapshots_to_delete = cursor.fetchall()
        conn.close()

        if snapshots_to_delete:
            console.print("[yellow]Database snapshots to delete:[/yellow]")
            for snap in snapshots_to_delete[:10]:  # Show first 10
                console.print(f"  • Snapshot #{snap[0]}: {snap[1]} (${snap[2]:,.2f})")
            if len(snapshots_to_delete) > 10:
                console.print(f"  ... and {len(snapshots_to_delete) - 10} more")
            console.print(f"  Total: {len(snapshots_to_delete)} snapshots\n")
            total_to_delete += len(snapshots_to_delete)
        else:
            console.print("[green]No old snapshots to delete[/green]\n")

    if total_to_delete == 0:
        console.print("[green]✓ Nothing to clean up![/green]")
        return

    if dry_run:
        console.print(f"[yellow]Dry run complete. Would delete {total_to_delete} items.[/yellow]")
        console.print("Run without --dry-run to actually delete.")
        return

    # Confirmation
    if not yes:
        console.print(f"[bold yellow]⚠ Warning: About to delete {total_to_delete} items[/bold yellow]")
        if not click.confirm("Do you want to proceed?"):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return

    # Actual deletion
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
    import subprocess
    import shutil

    # Check if streamlit is installed
    if not shutil.which('streamlit'):
        console.print("[red]Error: Streamlit is not installed.[/red]")
        console.print("Install with: [bold]pip install streamlit[/bold]")
        raise click.Abort()

    # Check if web app exists
    web_app_path = Path('web/app.py')
    if not web_app_path.exists():
        console.print("[yellow]Warning: Web dashboard is not yet implemented.[/yellow]")
        console.print("This feature is coming soon in a future release.")
        console.print("\nFor now, you can:")
        console.print("  • Use [bold]portfolio-tracker status[/bold] to view your portfolio")
        console.print("  • Open CSV files in Excel/Google Sheets for analysis")
        console.print("  • Query the SQLite database directly")
        raise click.Abort()

    console.print("[bold blue]Launching web dashboard...[/bold blue]")
    console.print("Dashboard will open in your browser at http://localhost:8501")

    try:
        subprocess.run(['streamlit', 'run', str(web_app_path)], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to launch dashboard: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.argument('output_file', type=click.Path(), required=False)
@click.option('--snapshot-id', '-s', type=int, help='Specific snapshot ID to export')
@click.option('--days', '-d', type=int, default=90, help='Export snapshots from last N days')
@click.option('--format', '-f', type=click.Choice(['csv', 'json']), default='csv', help='Output format')
@click.pass_context
def export(ctx, output_file, snapshot_id, days, format):
    """Export portfolio data to file"""
    config = ctx.obj['config']
    db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))

    import json
    import csv

    if snapshot_id:
        # Export specific snapshot
        holdings = db.get_holdings(snapshot_id)
        if not holdings:
            console.print(f"[red]No holdings found for snapshot #{snapshot_id}[/red]")
            return

        snapshots_to_export = [{'id': snapshot_id, 'holdings': holdings}]
    else:
        # Export from date range - get full snapshots, not just history tuples
        all_snapshots = db.get_snapshots(1000)  # Get many snapshots
        if not all_snapshots:
            console.print("[yellow]No snapshots found.[/yellow]")
            return

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        snapshots_to_export = []
        for snap in all_snapshots:
            snap_date = datetime.fromisoformat(snap['timestamp'])
            if snap_date >= cutoff_date:
                holdings = db.get_holdings(snap['id'])
                snapshots_to_export.append({
                    'id': snap['id'],
                    'timestamp': snap['timestamp'],
                    'total_value': snap['total_value'],
                    'holdings': holdings
                })

    # Generate output filename if not specified
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"portfolio_export_{timestamp}.{format}"

    output_path = Path(output_file)

    try:
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(snapshots_to_export, f, indent=2)
        else:  # csv
            if snapshot_id:
                # Single snapshot - flat CSV
                with open(output_path, 'w', newline='') as f:
                    if holdings:
                        writer = csv.DictWriter(f, fieldnames=holdings[0].keys())
                        writer.writeheader()
                        writer.writerows(holdings)
            else:
                # Multiple snapshots - include snapshot info
                with open(output_path, 'w', newline='') as f:
                    fieldnames = ['snapshot_id', 'timestamp', 'total_value'] + list(snapshots_to_export[0]['holdings'][0].keys() if snapshots_to_export[0]['holdings'] else [])
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for snap in snapshots_to_export:
                        for holding in snap['holdings']:
                            row = {
                                'snapshot_id': snap['id'],
                                'timestamp': snap.get('timestamp', ''),
                                'total_value': snap.get('total_value', 0),
                                **holding
                            }
                            writer.writerow(row)

        console.print(f"[green]✓ Exported to {output_path}[/green]")
        console.print(f"  Snapshots: {len(snapshots_to_export)}")

    except Exception as e:
        logger.exception("Export failed")
        console.print(f"[red]✗ Export failed: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['csv', 'json']), help='Input format (auto-detect if not specified)')
@click.pass_context
def import_data(ctx, input_file, format):
    """Import portfolio data from external file"""
    config = ctx.obj['config']
    db = DatabaseManager(config.get('database.path', 'fidelity_portfolio.db'))
    storage = StorageManager(config.get('storage.output_dir', '.'))

    import json
    import csv

    input_path = Path(input_file)

    # Auto-detect format
    if not format:
        format = 'json' if input_path.suffix == '.json' else 'csv'

    console.print(f"[bold blue]Importing data from {input_path}...[/bold blue]")

    try:
        if format == 'json':
            with open(input_path) as f:
                data = json.load(f)

            # Validate structure
            if 'accounts' in data and 'timestamp' in data:
                # Standard portfolio data format
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Save to storage
                files = storage.save_all(data, f"imported_{timestamp}")
                console.print(f"  ✓ Saved JSON: {files['json']}")
                console.print(f"  ✓ Saved CSV: {files['holdings_csv']}")

                # Save to database
                snapshot_id = db.save_snapshot(data)
                console.print(f"  ✓ Saved to database (snapshot #{snapshot_id})")

                console.print(f"\n[green]✓ Import complete![/green]")
            else:
                console.print("[red]Invalid JSON format. Expected 'accounts' and 'timestamp' fields.[/red]")
                raise click.Abort()

        else:  # CSV
            console.print("[yellow]CSV import not yet fully implemented.[/yellow]")
            console.print("Use JSON format for full portfolio import.")
            raise click.Abort()

    except Exception as e:
        logger.exception("Import failed")
        console.print(f"[red]✗ Import failed: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.option('--tail', '-n', type=int, default=50, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow logs in real-time')
@click.option('--level', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), help='Filter by log level')
@click.pass_context
def logs(ctx, tail, follow, level):
    """View application logs"""
    config = ctx.obj['config']
    log_file = Path(config.get('logging.file', 'logs/portfolio-tracker.log'))

    if not log_file.exists():
        console.print(f"[yellow]Log file not found: {log_file}[/yellow]")
        console.print("Run a command first to generate logs.")
        return

    console.print(f"[bold blue]Viewing logs: {log_file}[/bold blue]\n")

    if follow:
        # Follow mode - real-time tail
        console.print("[yellow]Following logs... (Ctrl+C to exit)[/yellow]\n")
        import subprocess
        try:
            cmd = ['tail', '-f', str(log_file)]
            if level:
                cmd = ['tail', '-f', str(log_file), '|', 'grep', level]
            subprocess.run(cmd)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped following logs[/yellow]")
    else:
        # Show last N lines
        with open(log_file) as f:
            lines = f.readlines()

        # Filter by level if specified
        if level:
            lines = [line for line in lines if level in line]

        # Show last N lines
        lines_to_show = lines[-tail:] if len(lines) > tail else lines

        for line in lines_to_show:
            # Color code by level
            if 'ERROR' in line:
                console.print(f"[red]{line.rstrip()}[/red]")
            elif 'WARNING' in line:
                console.print(f"[yellow]{line.rstrip()}[/yellow]")
            elif 'SUCCESS' in line:
                console.print(f"[green]{line.rstrip()}[/green]")
            else:
                console.print(line.rstrip())

        console.print(f"\n[dim]Showing last {len(lines_to_show)} lines (total: {len(lines)} lines)[/dim]")


@cli.command()
@click.pass_context
def cache(ctx):
    """Show enrichment cache information"""
    console.print("[bold blue]Enrichment Cache[/bold blue]\n")

    # Create enricher to access cache
    enricher = DataEnricher()

    # Try to load cache from previous runs (cache is in-memory, so this will be empty)
    cache_stats = enricher.get_cache_stats()

    console.print(f"[bold]Cache Statistics[/bold]")
    console.print(f"  Cached Tickers: {cache_stats['cached_tickers']}")
    console.print(f"  Cache Size: {cache_stats['cache_size_bytes']} bytes")

    if cache_stats['cached_tickers'] > 0:
        console.print(f"\n[bold]Cached Tickers[/bold]")
        for ticker in cache_stats['tickers'][:20]:  # Show first 20
            console.print(f"  • {ticker}")
        if len(cache_stats['tickers']) > 20:
            console.print(f"  ... and {len(cache_stats['tickers']) - 20} more")
    else:
        console.print("\n[yellow]No cached data. Run enrichment to populate cache.[/yellow]")

    console.print("\n[dim]Note: Cache is cleared between runs. Use --clear-cache flag with enrich command to force refresh.[/dim]")


if __name__ == '__main__':
    cli(obj={})
