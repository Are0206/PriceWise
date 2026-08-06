

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