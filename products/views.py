from django.db.models.aggregates import Min
from django.shortcuts import get_object_or_404, render

from .models import Category, Product
from .services import *

#RF-9: View product details
def view_product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

#RF-8: Compare product prices
def compare_product_prices(request, pk):
    product = get_object_or_404(Product, pk=pk)
    prices = product.prices.select_related('supermarket').order_by('amount')
    return render(request, 'products/compare_prices.html', {'product': product, 'prices': prices})

def index(request):
    query = request.GET.get('q', '')
    search_by = request.GET.get('search_by', 'product')
    category_filter = request.GET.get('category', '')
    min_price_raw = request.GET.get('min_price', '')
    max_price_raw = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '')

    min_price = parse_price(min_price_raw)
    max_price = parse_price(max_price_raw)

    products = Product.objects.annotate(cheapest_price=Min('prices__amount'))
    categories = Category.objects.all()

    products = filter_by_category(products, category_filter)       # RF-12
    products = search_products(products, query, search_by)          # RF-6 y RF-7
    products = filter_products_by_price_range(products, min_price, max_price) # RF-14
    products = sort_products_by_price(products, sort)                        # RF-13

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
