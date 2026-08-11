from decimal import Decimal

from .models import ShoppingList
from products.models import Price, Supermarket


def calculate_supermarket_totals(shopping_list: ShoppingList):
    totals = {}

    supermarkets = Supermarket.objects.all()

    for supermarket in supermarkets:

        total = Decimal("0.00")
        valid_supermarket = True

        for item in shopping_list.items.all():

            try:
                price = Price.objects.get(
                    product=item.product,
                    supermarket=supermarket
                )

                total += price.amount * item.quantity

            except Price.DoesNotExist:

                # El supermercado no vende uno de los productos
                valid_supermarket = False
                break

        if valid_supermarket:
            totals[supermarket] = total

    return totals


def calculate_estimated_savings(shopping_list: ShoppingList):
    
    totals = calculate_supermarket_totals(shopping_list)

    if len(totals) < 2:
        return Decimal("0.00")

    cheapest = min(totals.values())
    most_expensive = max(totals.values())

    return most_expensive - cheapest

def recommend_cheapest_supermarket(shopping_list: ShoppingList):

    totals = calculate_supermarket_totals(shopping_list)

    if not totals:
        return None

    return min(totals, key=totals.get)


def calculate_supermarket_breakdown(shopping_list: ShoppingList):
    """Per-supermarket cost using whatever items it actually carries.

    Unlike calculate_supermarket_totals, a supermarket missing some
    items is still included, with a total for the items it does have
    and a list of the ones it's missing. Sorted cheapest-first, with
    full-coverage supermarkets always ranked ahead of partial ones.
    """
    items = list(shopping_list.items.select_related('product').all())
    prices_by_supermarket = {}

    for price in Price.objects.filter(product__in=[item.product for item in items]).select_related('supermarket'):
        prices_by_supermarket.setdefault(price.supermarket_id, {})[price.product_id] = price.amount

    breakdown = []
    for supermarket in Supermarket.objects.all():
        supermarket_prices = prices_by_supermarket.get(supermarket.id, {})
        total = Decimal("0.00")
        missing = []

        for item in items:
            price = supermarket_prices.get(item.product_id)
            if price is None:
                missing.append(item.product)
            else:
                total += price * item.quantity

        if len(missing) == len(items):
            continue  # doesn't carry any of the items, not worth listing

        breakdown.append({
            'supermarket': supermarket,
            'total': total,
            'missing': missing,
            'complete': not missing,
        })

    breakdown.sort(key=lambda entry: (not entry['complete'], entry['total']))
    return breakdown
