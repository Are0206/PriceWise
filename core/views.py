from decimal import Decimal, InvalidOperation

from django.shortcuts import render

from products.models import Product, Category


def _parse_price(raw):
   
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def home(request):
    query = request.GET.get('q', '')
    search_by = request.GET.get('search_by', 'product')
    category_filter = request.GET.get('category', '')
    min_price_raw = request.GET.get('min_price', '')
    max_price_raw = request.GET.get('max_price', '')

    min_price = _parse_price(min_price_raw)
    max_price = _parse_price(max_price_raw)

    products = Product.objects.all()
    categories = Category.objects.all()

    if category_filter:
        products = products.filter(category__slug=category_filter)

  
    if query:
        match search_by:
            case 'supermarket':
                products = products.filter(prices__supermarket__name__icontains=query).distinct()
            case _:
                products = products.filter(name__icontains=query)

    if min_price is not None and max_price is not None:
        products = products.filter(
            prices__amount__gte=min_price,
            prices__amount__lte=max_price,
        ).distinct()
    elif min_price is not None:
        products = products.filter(prices__amount__gte=min_price).distinct()
    elif max_price is not None:
        products = products.filter(prices__amount__lte=max_price).distinct()

    return render(
        request,
        "core/index.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "search_by": search_by,
            "category_filter": category_filter,
            "min_price": min_price_raw,
            "max_price": max_price_raw,
        }
    )