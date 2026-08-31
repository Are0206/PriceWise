from decimal import Decimal, InvalidOperation

from django.db.models.aggregates import Min
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


def compare_prices(request, pk):
    product = get_object_or_404(Product, pk=pk)
    prices = product.prices.select_related('supermarket').order_by('amount')
    return render(request, 'products/compare_prices.html', {'product': product, 'prices': prices})

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

    sort = request.GET.get('sort', '')

    min_price = _parse_price(min_price_raw)
    max_price = _parse_price(max_price_raw)

    products = Product.objects.annotate(cheapest_price=Min('prices__amount'))
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

    match sort:
        case 'price_asc':
            products = products.order_by('cheapest_price')
        case 'price_desc':
            products = products.order_by('-cheapest_price')

    return render(
        request,
        "products/index.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "search_by": search_by,
            "category_filter": category_filter,
            "min_price": min_price_raw,
            "max_price": max_price_raw,
            "sort": sort,
        }
    )
