from decimal import Decimal

from django.utils import timezone

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


#RF-45: Gasto por categoría en el supermercado recomendado
def calculate_category_breakdown(shopping_list: ShoppingList, best_entry):
    """Cuánto cuesta cada categoría comprando la lista en el supermercado recomendado.

    Usa los precios de ese supermercado para que las barras sumen exactamente
    el total que la página ya muestra. Los productos que ese supermercado no
    vende no se pueden contar: se devuelven aparte para avisarlo en pantalla.

    Devuelve (lista de categorías ordenada de mayor a menor, productos excluidos).
    """
    if best_entry is None:
        return [], []

    items = list(shopping_list.items.select_related('product__category').all())
    if not items:
        return [], []

    prices = {
        price.product_id: price.amount
        for price in Price.objects.filter(
            supermarket=best_entry['supermarket'],
            product__in=[item.product for item in items],
        )
    }

    totals = {}
    excluded = []

    for item in items:
        amount = prices.get(item.product_id)
        if amount is None:
            excluded.append(item.product)
            continue
        category = item.product.category
        totals[category] = totals.get(category, Decimal("0.00")) + amount * item.quantity

    grand_total = sum(totals.values(), Decimal("0.00"))
    if grand_total == 0:
        return [], excluded

    breakdown = [
        {
            'category': category,
            'total': total,
            # Porcentaje sobre el total contado, no sobre el total de la lista.
            'percentage': (total / grand_total * 100).quantize(Decimal("0.1")),
        }
        for category, total in totals.items()
    ]
    breakdown.sort(key=lambda entry: entry['total'], reverse=True)

    return breakdown, excluded

# PriceWise Wrapped: savings summary across all of a user's lists.
# Spec: docs/superpowers/specs/2026-10-30-wrapped-design.md
def _profile(saved_pct):
    """Under 5 %, from 5 % to 15 %, and over 15 % (spec thresholds)."""
    if saved_pct > 15:
        return {'title': 'Cazador de ofertas', 'text': 'Ahorras más del 15 % en cada mercado.'}
    if saved_pct >= 5:
        return {'title': 'Buen ojo', 'text': 'Comparar te está saliendo a cuenta.'}
    return {'title': 'Comprador tranquilo', 'text': 'Con más listas vas a ver cuánto puedes ahorrar.'}


def build_wrapped(user):
    """Every number of the Wrapped, compared product by product.

    For each item: "with" is the cheapest current price x quantity, "without"
    the most expensive one. Products priced in a single store add to spending
    but save nothing; products with no price are only counted. Three queries,
    whatever the number of lists or items.
    """
    from products.models import Price
    from .models import ShoppingListItem

    lists = list(ShoppingList.objects.filter(owner=user).order_by('created_at', 'pk'))
    items = list(ShoppingListItem.objects.filter(shopping_list__in=lists)
                 .select_related('product__category'))
    prices = {}
    for price in (Price.objects.filter(product__in={item.product_id for item in items})
                  .select_related('supermarket')):
        prices.setdefault(price.product_id, []).append(price)

    per_list = {sl.pk: {'name': sl.name, 'created_at': sl.created_at,
                        'with': Decimal('0'), 'without': Decimal('0')} for sl in lists}
    wins, category_saved, gaps, lists_with = {}, {}, {}, {}
    unpriced = units = 0

    for item in items:
        units += item.quantity
        lists_with.setdefault(item.product_id, set()).add(item.shopping_list_id)
        options = prices.get(item.product_id)
        if not options:
            unpriced += 1
            continue
        # Ties go to the supermarket with the lowest pk, so the result is stable.
        cheapest = min(options, key=lambda p: (p.amount, p.supermarket_id))
        dearest = max(p.amount for p in options)
        row = per_list[item.shopping_list_id]
        row['with'] += cheapest.amount * item.quantity
        row['without'] += dearest * item.quantity
        if len(options) >= 2:
            store = cheapest.supermarket
            wins[store.pk] = (store.name, wins.get(store.pk, (store.name, 0))[1] + 1)
            category = item.product.category.name
            category_saved[category] = category_saved.get(category, 0) + (dearest - cheapest.amount) * item.quantity
            gaps[item.product_id] = (item.product.name, dearest - cheapest.amount)

    rows = list(per_list.values())
    total_with = sum((r['with'] for r in rows), Decimal('0'))
    total_without = sum((r['without'] for r in rows), Decimal('0'))
    saved = total_without - total_with
    saved_pct = (saved / total_without * 100).quantize(Decimal('0.1')) if total_without else Decimal('0')

    ranking = sorted(wins.items(), key=lambda kv: (-kv[1][1], kv[0]))
    top_category = max(category_saved.items(), key=lambda kv: kv[1], default=None)
    star = max(gaps.items(), key=lambda kv: (kv[1][1], -kv[0]), default=None)

    return {
        'list_count': len(lists),
        # Local dates (America/Bogota), not UTC: a list made at 8 p. m. stays on its own day.
        'first_date': timezone.localdate(lists[0].created_at) if lists else None,
        'last_date': timezone.localdate(lists[-1].created_at) if lists else None,
        'total_with': total_with,
        'total_without': total_without,
        'saved': saved,
        'saved_pct': saved_pct,
        'per_list': rows,
        'top_store': ({'name': ranking[0][1][0], 'wins': ranking[0][1][1], 'of': sum(w for _, w in wins.values())}
                      if ranking else None),
        'runner_up': {'name': ranking[1][1][0], 'wins': ranking[1][1][1]} if len(ranking) > 1 else None,
        'top_category': {'name': top_category[0], 'saved': top_category[1]} if top_category else None,
        'star_product': ({'name': star[1][0], 'gap': star[1][1], 'lists': len(lists_with[star[0]])}
                         if star else None),
        'distinct_products': len(lists_with),
        'units': units,
        'avg_per_list': (total_with / len(lists)).quantize(Decimal('0.01')) if lists else Decimal('0'),
        'unpriced_items': unpriced,
        'profile': _profile(saved_pct),
    }


# Validated with the dataviz palette checker on the cream background (#FAF8F6):
# green/blue passes every check. Green/red failed for deuteranopia (ΔE 2.5), so
# "without" is blue, dashed, and both lines carry direct labels.
WRAPPED_COLORS = {'with': '#1A7F37', 'without': '#2a78d6'}
WRAPPED_W, WRAPPED_H = 320, 220
WRAPPED_PLOT = {'left': 12, 'right': 228, 'top': 16, 'bottom': 188}


def wrapped_chart(per_list):
    """Cumulative spending, list by list, as SVG geometry. None with fewer than 2 lists."""
    if len(per_list) < 2:
        return None
    cum_with, cum_without, total_with, total_without = [], [], Decimal('0'), Decimal('0')
    for row in per_list:
        total_with += row['with']
        total_without += row['without']
        cum_with.append(total_with)
        cum_without.append(total_without)

    left, right, top, bottom = (WRAPPED_PLOT[k] for k in ('left', 'right', 'top', 'bottom'))
    peak = cum_without[-1] or Decimal('1')
    step = (right - left) / (len(per_list) - 1)

    def point(i, amount):
        return round(left + i * step, 1), round(bottom - float(amount / peak) * (bottom - top), 1)

    with_pts = [point(i, a) for i, a in enumerate(cum_with)]
    without_pts = [point(i, a) for i, a in enumerate(cum_without)]
    as_text = lambda pts: ' '.join(f'{x},{y}' for x, y in pts)
    return {
        'width': WRAPPED_W,
        'height': WRAPPED_H,
        'plot': WRAPPED_PLOT,
        'with_points': as_text(with_pts),
        'without_points': as_text(without_pts),
        'area_points': as_text(without_pts + with_pts[::-1]),
        'labels': [{'x': with_pts[0][0], 'text': 'Compra 1'},
                   {'x': with_pts[-1][0], 'text': f'Compra {len(per_list)}'}],
        # Direct labels at the line ends; pushed apart when the lines nearly touch.
        'end': {'x': right + 8, 'without_y': without_pts[-1][1],
                'with_y': max(with_pts[-1][1], without_pts[-1][1] + 14)},
        'colors': WRAPPED_COLORS,
    }
