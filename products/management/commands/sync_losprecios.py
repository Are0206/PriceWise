"""Django management command that runs the Los Precios pipeline.

Entry point for manual runs and scheduled jobs (cron, GitHub Actions).
Only parses command-line arguments (store, stage, dry run) and delegates
to the pipeline. Contains no business logic.

Usage: python manage.py sync_losprecios [options]
"""