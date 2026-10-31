from decimal import Decimal, InvalidOperation

from .models import Supermarket, normalize_search_text

def parse_price(raw):
    """Price filter from the query string; anything that is not a finite, non-negative number is ignored."""
    if not raw:
        return None
    try:
        price = Decimal(raw.strip())
    except InvalidOperation:
        return None
    # NaN and Infinity parse as Decimals but crash the database filter.
    if not price.is_finite() or price < 0:
        return None
    return price

# RF-12: Filter products by category
def filter_by_category(products, category_slug):
    if category_slug:
        return products.filter(category__slug=category_slug)
    return products


# RF-6: Search products by name
# RF-7: Search products by supermarket
def search_products(products, query, search_by):
    if not query:
        return products
        
    needle = normalize_search_text(query.strip())
    match search_by:
        case 'supermarket':
            # RF-7: Search products by supermarket. There are only a handful of
            # supermarkets, so their names are compared in Python, without accents.
            supermarket_ids = [s.pk for s in Supermarket.objects.only('pk', 'name')
                               if needle in normalize_search_text(s.name)]
            return products.filter(prices__supermarket__in=supermarket_ids).distinct()
        case _:
            # RF-6: Search products by name, ignoring accents and case
            return products.filter(search_name__contains=needle)


# RF-14: Filter products by price range
def filter_products_by_price_range(products, min_price, max_price):
    if min_price is not None and max_price is not None:
        return products.filter(
            prices__amount__gte=min_price, 
            prices__amount__lte=max_price
        ).distinct()
    elif min_price is not None:
        return products.filter(prices__amount__gte=min_price).distinct()
    elif max_price is not None:
        return products.filter(prices__amount__lte=max_price).distinct()
    return products


# RF-13: Sort products by price
def sort_products_by_price(products, sort_option):
    match sort_option:
        case 'price_asc':
            return products.order_by('cheapest_price', 'name', 'id')
        case 'price_desc':
            return products.order_by('-cheapest_price', 'name', 'id')
    return products.order_by('name', 'id')

# RF-32 extension: price history of a product, one line per supermarket.
# Categorical slots validated with the dataviz palette checker on the white card
# (all hard checks pass; two hues sit below 3:1, so the chart always ships with
# direct labels and a table view).
SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
CHART_WIDTH, CHART_HEIGHT = 640, 240
PLOT_LEFT, PLOT_RIGHT, PLOT_TOP, PLOT_BOTTOM = 72, 520, 16, 204


def price_history(product):
    """Series and chart geometry for the product detail page.

    Returns {'series', 'has_chart', 'y_ticks', 'x_ticks'}. A chart needs at least two
    different dates; with a single observation the page only shows the table.
    Colors follow the supermarket (its position among all supermarkets), never
    its rank on this product, so D1 has the same color on every page.
    """
    from pricewise.templatetags.money import money
    from .models import PriceHistory

    color_by_store = {pk: SERIES_COLORS[i % len(SERIES_COLORS)]
                      for i, pk in enumerate(Supermarket.objects.order_by('pk').values_list('pk', flat=True))}
    rows = (PriceHistory.objects.filter(price__product=product)
            .select_related('price__supermarket')
            .order_by('price__supermarket__name', 'price_date'))

    series = {}
    for row in rows:
        store = row.price.supermarket
        entry = series.setdefault(store.pk, {'name': store.name, 'color': color_by_store.get(store.pk, '#6b6964'),
                                             'current': row.price.amount, 'points': []})
        entry['points'].append({'date': row.price_date, 'amount': row.amount})
    series = list(series.values())

    for entry in series:
        first = entry['points'][0]
        entry['first'] = first
        # The current price is the Price row; history only records changes.
        entry['change'] = entry['current'] - first['amount']
        entry['change_pct'] = (entry['change'] / first['amount'] * 100) if first['amount'] else None

    dates = sorted({p['date'] for entry in series for p in entry['points']})
    result = {'series': series, 'has_chart': len(dates) >= 2, 'y_ticks': [], 'x_ticks': [],
              'width': CHART_WIDTH, 'height': CHART_HEIGHT,
              'plot': {'left': PLOT_LEFT, 'right': PLOT_RIGHT, 'top': PLOT_TOP, 'bottom': PLOT_BOTTOM}}
    if not result['has_chart']:
        return result

    amounts = [p['amount'] for entry in series for p in entry['points']]
    low, high = min(amounts), max(amounts)
    pad = (high - low) * Decimal('0.1') or high * Decimal('0.05') or Decimal(1)
    low, high = max(low - pad, Decimal(0)), high + pad
    first_day, span = dates[0], (dates[-1] - dates[0]).days

    def x(day):
        return PLOT_LEFT + (day - first_day).days / span * (PLOT_RIGHT - PLOT_LEFT)

    def y(amount):
        return PLOT_BOTTOM - float((amount - low) / (high - low)) * (PLOT_BOTTOM - PLOT_TOP)

    for entry in series:
        for p in entry['points']:
            p['x'], p['y'] = round(x(p['date']), 1), round(y(p['amount']), 1)
            p['label'] = f"{entry['name']}, {p['date']:%d/%m/%Y}: ${money(p['amount'])}"
        entry['path'] = ' '.join(f"{p['x']},{p['y']}" for p in entry['points'])

    # Direct labels at the end of each line, pushed apart so they never overlap.
    labelled = sorted(series, key=lambda e: e['points'][-1]['y'])
    previous = None
    for entry in labelled:
        label_y = entry['points'][-1]['y']
        if previous is not None and label_y - previous < 14:
            label_y = previous + 14
        entry['label_y'] = round(label_y, 1)
        previous = label_y

    steps = 4
    result['y_ticks'] = [{'y': round(y(low + (high - low) * i / steps), 1),
                          'label': f"${money(low + (high - low) * i / steps).split(',')[0]}"}
                         for i in range(steps + 1)]
    shown = dates if len(dates) <= 6 else [dates[0], dates[len(dates) // 2], dates[-1]]
    result['x_ticks'] = [{'x': round(x(d), 1), 'label': f"{d:%d/%m}"} for d in shown]
    return result
