from decimal import Decimal, InvalidOperation

def parse_price(raw):
   
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None

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
        
    match search_by:
        case 'supermarket':
            # RF-7: Search products by supermarket
            return products.filter(prices__supermarket__name__icontains=query).distinct()
        case _:
            # RF-6: Search products by name
            return products.filter(name__icontains=query)


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
            return products.order_by('cheapest_price')
        case 'price_desc':
            return products.order_by('-cheapest_price')
    return products