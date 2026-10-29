"""Orchestrates the Los Precios import, stage by stage.

Defines the order of the stages (supermarkets, catalog, prices), connects
the client, the normalizers and the loaders, and decides how to handle
partial failures so that one failing store does not abort the whole run.
Each stage can be executed on its own. Logs a summary at the end of each run.
"""
#RF-40: Store and update products and prices API data
import logging
from collections import Counter

from .client import LosPreciosError
from .loaders import load_products, load_supermarkets
from .normalizers import normalize_page, normalize_supermarkets

logger = logging.getLogger(__name__)


def sync_supermarkets(client):
    """Stage 1: fetch and store the supermarkets. Returns {api_id: Supermarket}."""
    return load_supermarkets(normalize_supermarkets(client.get_supermarkets()))


def sync_store_products(client, store_api_id, supermarkets_by_api_id, max_pages=None):
    """Stage 2: walk every page of one store's catalog and store its products and prices."""
    totals = Counter()
    seen = 0
    page = 1
    while max_pages is None or page <= max_pages:
        data = normalize_page(client.get_supermarkets_details(id=store_api_id, page=page))
        if data["items_on_page"] == 0:
            break
        totals.update(load_products(data["products"], supermarkets_by_api_id))
        totals["pages"] += 1
        seen += data["items_on_page"]
        if data["total_items"] is not None and seen >= data["total_items"]:
            break
        page += 1
    return totals


def run(client, store_api_ids=None, max_pages=None):
    """Run the whole import. A failing store is logged and skipped; a fatal API error stops the run."""
    supermarkets_by_api_id = sync_supermarkets(client)
    totals = Counter()
    failed = []
    for api_id, supermarket in supermarkets_by_api_id.items():
        if store_api_ids and api_id not in store_api_ids:
            continue
        try:
            totals.update(sync_store_products(client, api_id, supermarkets_by_api_id, max_pages))
        except LosPreciosError as error:
            if error.is_fatal:
                raise
            logger.error("Store %s (%s) failed: %s", supermarket.name, api_id, error)
            failed.append(supermarket.name)

    logger.info("Los Precios import: %s; failed stores: %s", dict(totals), failed or "none")
    return {"supermarkets": len(supermarkets_by_api_id), "failed_stores": failed, **totals}
