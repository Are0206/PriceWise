from decimal import Decimal

from .models import ShoppingList
from products.models import Price, Supermarket


def calculate_supermarket_breakdown(shopping_list: ShoppingList):
    """Per-supermarket cost using whatever items it actually carries.

    A supermarket missing some items is still included, with a total
    for the items it does have and a list of the ones it's missing.
    Sorted cheapest-first, with full-coverage supermarkets always
    ranked ahead of partial ones.
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

        if len(missing) == len(items) and len(items) > 0:
            continue

        breakdown.append({
            'supermarket': supermarket,
            'total': total,
            'missing': missing,
            'complete': not missing,
        })

    return breakdown

#RF-2: Recommend cheapest supermarket
def get_cheapest_supermarket_recommendation(breakdown):
    sorted_breakdown = sorted(breakdown, key=lambda entry: (not entry['complete'], entry['total']))
    best_supermarket = sorted_breakdown[0] if sorted_breakdown else None
    
    return sorted_breakdown, best_supermarket

#RF-3: Calculate estimated savings
def calculate_estimated_savings(sorted_breakdown):
    complete_entries = [entry for entry in sorted_breakdown if entry['complete']]
    
    if len(complete_entries) >= 2:
        return complete_entries[-1]['total'] - complete_entries[0]['total']
    return None
