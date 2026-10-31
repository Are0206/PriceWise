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