"""Writes normalized Los Precios data into the Django models.

The only module (together with the pipeline) that touches the database.
Performs idempotent upserts of supermarkets, categories, products and
current prices, and inserts a PriceHistory row only when the amount or the
price date changes. Price updates and their history are written inside a
single transaction to keep both in sync.
"""
#RF-40: Store and update products and prices API data
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from products.models import Category, Price, PriceHistory, Product, Supermarket

logger = logging.getLogger(__name__)

# Used only when products are loaded without an API category.
DEFAULT_CATEGORY_NAME = "Otros"


def load_supermarkets(supermarkets):
    """Upsert normalized supermarkets. Returns {api_id: Supermarket}.

    A supermarket that already exists with the same name (for example one
    created by hand in the admin) is linked to its API id instead of duplicated.
    """
    by_api_id = {}
    for data in supermarkets:
        supermarket = Supermarket.objects.filter(api_id=data["api_id"]).first()
        if supermarket is None:
            supermarket = Supermarket.objects.filter(name__iexact=data["name"], api_id__isnull=True).first()
        if supermarket is None:
            supermarket = Supermarket(name=data["name"])
        supermarket.api_id = data["api_id"]
        try:
            # A savepoint per store: a name clash rolls back only this store
            # and leaves the surrounding transaction usable for the next one.
            with transaction.atomic():
                supermarket.save()
        except IntegrityError as error:
            logger.error("Skipping supermarket %r (API id %s): %s", data["name"], data["api_id"], error)
            continue
        by_api_id[data["api_id"]] = supermarket
    return by_api_id


def load_products(products, supermarkets_by_api_id, price_date=None, category_name=None):
    """Upsert normalized products and their prices.

    category_name is the API category the products were fetched from; it is
    set on every product so the API stays the source of truth. Without it,
    new products go to the default category and existing ones keep theirs.

    Returns counts: created, updated, prices_changed, skipped_prices.
    Each product and its prices are saved in one transaction, so a failure
    on one product does not leave half-written prices behind.
    """
    price_date = price_date or timezone.localdate()
    stats = {"created": 0, "updated": 0, "prices_changed": 0, "skipped_prices": 0}
    category = _category(category_name) if category_name else None

    for data in products:
        with transaction.atomic():
            product = Product.objects.filter(api_id=data["api_id"]).first()
            if product is None:
                if category is None:
                    category = _category(DEFAULT_CATEGORY_NAME)
                product = Product(api_id=data["api_id"], category=category)
                stats["created"] += 1
            else:
                stats["updated"] += 1
                if category_name:
                    product.category = category
            product.name = data["name"][:200]
            product.description = data.get("description") or ""
            product.image_url = data.get("image_url") or ""
            product.save()

            for price_data in data["prices"]:
                supermarket = supermarkets_by_api_id.get(price_data["supermarket_api_id"])
                if supermarket is None:
                    logger.warning("Skipping price for unknown supermarket %s (product %s)",
                                   price_data["supermarket_api_id"], data["api_id"])
                    stats["skipped_prices"] += 1
                    continue
                if _save_price(product, supermarket, price_data["amount"], price_date):
                    stats["prices_changed"] += 1

    return stats


def _save_price(product, supermarket, amount, price_date):
    """Set the current price and record it in the history if it changed.

    Returns True when the amount is new or different from the last observation.
    """
    price, created = Price.objects.get_or_create(
        product=product, supermarket=supermarket, defaults={"amount": amount})
    last = price.history.first()  # newest first (PriceHistory.Meta.ordering)
    if not created and last is not None and last.amount == amount:
        return False

    if price.amount != amount:
        price.amount = amount
        price.save(update_fields=["amount", "updated_at"])
    # One observation per price and day: a second change on the same day replaces it.
    PriceHistory.objects.update_or_create(
        price=price, price_date=price_date, defaults={"amount": amount})
    return True


def _category(name):
    """Find a category by name (or slug, for ones created by hand) or create it."""
    slug = slugify(name)
    category = Category.objects.filter(name__iexact=name).first() or Category.objects.filter(slug=slug).first()
    if category is None:
        category = Category.objects.create(name=name, slug=slug)
    return category
