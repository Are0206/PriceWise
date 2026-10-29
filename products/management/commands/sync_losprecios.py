"""Django management command that runs the Los Precios pipeline.

Entry point for manual runs and scheduled jobs (cron, GitHub Actions).
Only parses command-line arguments (store, stage, dry run) and delegates
to the pipeline. Contains no business logic.

Usage: python manage.py sync_losprecios [options]
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from products.integrations.lospreciosco import pipeline
from products.integrations.lospreciosco.client import LosPreciosClient, LosPreciosError


def read_api_key():
    """The key comes from the environment or from the project's .env file, never from the code."""
    key = os.environ.get("LOSPRECIOS_API_KEY")
    env_file = settings.BASE_DIR / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "LOSPRECIOS_API_KEY":
                key = value.strip().strip('"').strip("'")
    return key


class Command(BaseCommand):
    help = "Import supermarkets, products and prices from the Los Precios API."

    def add_arguments(self, parser):
        parser.add_argument("--store", type=int, action="append",
                            help="Only import this store's API id (can be repeated).")
        parser.add_argument("--max-pages", type=int,
                            help="Stop after this many catalog pages per store (useful for a quick test).")
        parser.add_argument("--category", action="append",
                            help="Only import this API category, e.g. Despensa (can be repeated).")
        parser.add_argument("--only-supermarkets", action="store_true",
                            help="Only import the list of supermarkets.")

    def handle(self, *args, **options):
        try:
            client = LosPreciosClient(read_api_key())
            if options["only_supermarkets"]:
                stores = pipeline.sync_supermarkets(client)
                self.stdout.write(self.style.SUCCESS(f"{len(stores)} supermarkets imported."))
                return
            summary = pipeline.run(client, store_api_ids=options["store"], max_pages=options["max_pages"],
                                   categories=options["category"])
        except LosPreciosError as error:
            raise CommandError(f"Los Precios API: {error}") from error

        self.stdout.write(self.style.SUCCESS(
            f"{summary['supermarkets']} supermarkets, {summary.get('pages', 0)} pages: "
            f"{summary.get('created', 0)} products created, {summary.get('updated', 0)} updated, "
            f"{summary.get('prices_changed', 0)} prices changed, "
            f"{summary.get('skipped_prices', 0)} prices skipped."))
        if summary["failed_stores"]:
            self.stdout.write(self.style.WARNING("Failed: " + ", ".join(summary["failed_stores"])))
