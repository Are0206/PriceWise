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

# The API filters a store's catalog by category name but has no endpoint that
# lists them. shortcut: names copied from losprecios.co/mercado on 2026-10-29;
# update this list if the site adds or renames a category.
CATEGORIES = [
    "Despensa", "Bebidas", "Frutas y Verduras", "Carnes y Pescados", "Panadería",
    "Comida Preparada", "Refrigerados", "Dulces y Pasabocas", "Cuidado Personal",
    "Aseo del Hogar", "Licores", "Bebés", "Mascotas", "Varios",
]

# Supermarkets that do not expose products in the Los Precios API (e.g. Éxito ID 6).
# Skipping them prevents making redundant requests (14 categories per run).
SUPERMARKETS_WITHOUT_PRODUCTS = {6}


# Safety cap so a provider bug (pages that never come back empty) cannot loop forever.
# A full run in October 2026 was 625 pages across every store and category.
MAX_PAGES_PER_CATEGORY = 200


def sync_supermarkets(client):
    """Stage 1: fetch and store the supermarkets. Returns {api_id: Supermarket}."""
    return load_supermarkets(normalize_supermarkets(client.get_supermarkets()))


def sync_store_products(client, store_api_id, supermarkets_by_api_id, max_pages=None, category=None):
    """Stage 2: walk every page of one store's catalog (optionally one category) and store it."""
    totals = Counter()
    seen = 0
    page = 1
    while max_pages is None or page <= max_pages:
        if page > MAX_PAGES_PER_CATEGORY:
            logger.warning("Store %s, category %s: stopped at the %d-page safety cap; the import is incomplete.",
                           store_api_id, category, MAX_PAGES_PER_CATEGORY)
            totals["truncated"] += 1
            break
        data = normalize_page(client.get_supermarkets_details(id=store_api_id, category=category, page=page))
        if data["items_on_page"] == 0:
            break
        totals.update(load_products(data["products"], supermarkets_by_api_id, category_name=category))
        totals["pages"] += 1
        seen += data["items_on_page"]
        if data["total_items"] is not None and seen >= data["total_items"]:
            break
        page += 1
    return totals


def run(client, store_api_ids=None, max_pages=None, categories=None):
    """Run the whole import, store by store and category by category.

    A failing store or category is logged and skipped; a fatal API error stops the run.
    """
    supermarkets_by_api_id = sync_supermarkets(client)
    totals = Counter()
    failed = []
    truncated = []
    for api_id, supermarket in supermarkets_by_api_id.items():
        if store_api_ids and api_id not in store_api_ids:
            continue
        if api_id in SUPERMARKETS_WITHOUT_PRODUCTS and not store_api_ids:
            logger.info("Skipping supermarket %s (ID %s): no products available in API.", supermarket.name, api_id)
            continue
        for category in categories or CATEGORIES:
            try:
                store_totals = sync_store_products(client, api_id, supermarkets_by_api_id, max_pages, category)
                if store_totals.pop("truncated", 0):
                    truncated.append(f"{supermarket.name} / {category}")
                totals.update(store_totals)
            except LosPreciosError as error:
                if error.is_fatal:
                    raise
                logger.error("Store %s (%s), category %s failed: %s", supermarket.name, api_id, category, error)
                failed.append(f"{supermarket.name} / {category}")

    logger.info("Los Precios import: %s; failed stores: %s; truncated: %s",
                dict(totals), failed or "none", truncated or "none")
    return {"supermarkets": len(supermarkets_by_api_id), "failed_stores": failed, "truncated": truncated, **totals}
