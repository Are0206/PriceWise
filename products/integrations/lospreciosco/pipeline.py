from client import LosPreciosClient, LosPreciosError
from normalizers import normalize_supermarkets, normalize_page

import logging
import os

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Despensa",
    "Bebidas",
    "Frutas y Verduras",
    "Carnes y Pescados",
    "Panadería",
    "Comida Preparada",
    "Refrigerados",
    "Dulces y Pasabocas",
    "Cuidado Personal",
    "Aseo del Hogar",
    "Licores",
    "Bebés",
    "Mascotas",
    "Varios",
]

# Supermarket ID 6 has no products available.
SUPERMARKETS_WITHOUT_PRODUCTS = {6}


client = LosPreciosClient(api_key=os.environ['LOSPRECIOS_API_KEY'])

# IMPORT SUPERMARKETS
def import_supermarkets(client):
    supermarkets_json = client.get_supermarkets()
    supermarkets = normalize_supermarkets(supermarkets_json) #supermarkets[i][{"api_id", "name"}]

    """
    TODO: save in database
    for supermarket in supermarkets:
        #save
    """

    logger.info("Found %d supermarkets.", len(supermarkets))
    return supermarkets

def import_products(client, supermarkets):
    total_supermarkets = len(supermarkets)

    for index, supermarket in enumerate(supermarkets, start=1):
        supermarket_id = supermarket["api_id"]

        if supermarket_id in SUPERMARKETS_WITHOUT_PRODUCTS:
            logger.info(
                "Skipping supermarket %s (ID %s): no products available.",
                supermarket["name"],
                supermarket_id,
            )
            continue

        logger.info(
            "Importing products from supermarket %s/%s: %s",
            index,
            total_supermarkets,
            supermarket["name"],
        )

        try:
            import_supermarket_products(client, supermarket)
        except LosPreciosError as exc:
            if exc.is_fatal:
                raise

            logger.exception(
                "Could not import supermarket %s (ID %s).",
                supermarket["name"],
                supermarket_id,
            )
            continue

def import_supermarket_products(client, supermarket):
    supermarket_id = supermarket["api_id"]

    for category in CATEGORIES:
        try:
            import_category_products(client, supermarket, category)
        except LosPreciosError as exc:
            if exc.is_fatal:
                raise

            logger.exception(
                "Failed category '%s' for supermarket %s (ID %s).",
                category,
                supermarket["name"],
                supermarket_id,
            )


def import_category_products(client, supermarket, category):
    supermarket_id = supermarket["api_id"]
    page_index = 1
    products_count = 0

    while True:
        page_json = client.get_supermarket_category_page(
            id=supermarket_id,
            category=category,
            page=page_index,
        )

        page = normalize_page(page_json)
        total_items = page["total_items"]
        items_on_page = page["items_on_page"]
        products = page["products"]

        #Empty first page means nothing to import.
        if page_index == 1 and items_on_page == 0:
            logger.info(
                "No products in category '%s' for supermarket %s.",
                category,
                supermarket["name"],
            )
            break

        # TODO: Save or update normalized products and their prices.
    

        products_count += items_on_page

        if items_on_page == 0:
            break

        if total_items is not None and products_count >= total_items:
            break

        # Without a total, continue until an empty page is returned.
        page_index += 1

    logger.info(
        "Imported %s items from category '%s' in supermarket %s.",
        products_count,
        category,
        supermarket["name"],
    )
                
