"""Removes the hand-made demo catalog once real data comes from the Los Precios API.

Demo rows are the ones without an API id: products, supermarkets (and their
prices, reviews, favorites and locations, which cascade) and categories left
with no products. Shopping list items that point to demo products are removed
first, because the list item foreign key protects products from deletion.

Shows what would be deleted and only deletes with --yes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Category, Product, Supermarket
from shopping_lists.models import ShoppingListItem


class Command(BaseCommand):
    help = "Delete demo products, supermarkets and empty categories (rows without an API id)."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Actually delete; without it only reports.")

    def handle(self, *args, **options):
        products = Product.objects.filter(api_id__isnull=True)
        supermarkets = Supermarket.objects.filter(api_id__isnull=True)
        list_items = ShoppingListItem.objects.filter(product__in=products)
        if not Product.objects.filter(api_id__isnull=False).exists():
            self.stdout.write(self.style.ERROR("No imported products yet: run sync_losprecios first."))
            return

        self.stdout.write(
            f"Demo products: {products.count()}, demo supermarkets: "
            f"{', '.join(supermarkets.values_list('name', flat=True)) or 'none'}, "
            f"shopping list items using demo products: {list_items.count()}.")
        if not options["yes"]:
            self.stdout.write("Nothing deleted. Run again with --yes to delete.")
            return

        with transaction.atomic():
            list_items.delete()
            products.delete()
            supermarkets.delete()
            empty = Category.objects.filter(products__isnull=True)
            empty_names = list(empty.values_list("name", flat=True))
            empty.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Demo data removed. Empty categories deleted: {', '.join(empty_names) or 'none'}."))
