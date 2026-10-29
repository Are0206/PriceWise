#RF-39: Validate and normalizate API data
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

def _clean_text(value):
    if not isinstance(value, str):
        return None
    return value.strip() or None

def normalize_supermarkets(supermarkets_json):
    supermarkets_normalized = []

    for supermarket_json in supermarkets_json or []:
        api_id = supermarket_json.get("ID")
        name = _clean_text(supermarket_json.get("Nombre"))

        if api_id is None or not name:
            logger.warning("Skipping supermarket with missing ID or name: %s", supermarket_json)
            continue

        supermarkets_normalized.append({"api_id": api_id, "name": name})

    return supermarkets_normalized

def normalize_page(page_json):
    total_items
    pass     

def _normalize_products(products_json):
    products_normalized = []

    for product_json in products_json or []:
        api_id = product_json.get("ID")
        name = _clean_text(product_json.get("Producto"))

        if api_id is None or not name:
            logger.warning("Skipping product with missing ID or name: %s", product_json)
            continue
            
        #Prices
        prices = []
        for price_json in product_json.get("ÍtemsTiendas") or []:
            supermarket_id = price_json.get("TiendaID")
            price = price_json.get("Precio")

            if price is None or supermarket_id is None:
                logger.warning("Skipping price with missing price value or supermarket: %s", price_json)
                continue
            
            try:
                amount = Decimal(str(price))
            except InvalidOperation:
                amount = None
            if amount is None or not amount.is_finite() or amount <= 0:
                logger.warning("Skipping price with invalid amount: %s", price_json)
                continue
            prices.append({"supermarket_api_id": supermarket_id, "amount": amount})
        
        if not prices:
            logger.warning("Skipping product with missing prices: %s", product_json)
            continue
        
        brand = _clean_text(product_json.get("Marca"))
        unit = _clean_text(product_json.get("Unidad"))
        size = product_json.get("Tamaño")
        complement = _clean_text(product_json.get("Complemento"))
        
        #image
        image_url = _clean_text(product_json.get("RutaImagen"))
        if image_url and "imagen-no-disponible" in image_url:
            image_url = None

        # 200.0 -> "200", 1.5 -> "1.5"
        size_text = None
        if isinstance(size, (int, float)) and size > 0:
            size_text = str(int(size)) if size == int(size) else str(size)

        description_lines = []
        if complement:
            description_lines.append(f"{name} {complement}")
        if brand:
            description_lines.append(f"marca: {brand}")
            name = f"{name} {brand}"
        if size_text:
            description_lines.append(f"tamaño: {size_text}{unit or ''}")
            name = f"{name} {size_text}{unit or ''}"
        description = "\n".join(description_lines)
        
        products_normalized.append({
            "api_id": api_id,
            "name": name,
            "description": description,
            "image_url": image_url,
            "prices": prices
        })

    return products_normalized