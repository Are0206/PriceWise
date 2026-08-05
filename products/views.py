from django.shortcuts import get_object_or_404, render

from .models import Product


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


def compare_prices(request, pk):
    product = get_object_or_404(Product, pk=pk)
    prices = product.prices.select_related('supermarket').order_by('amount')
    return render(request, 'products/compare_prices.html', {'product': product, 'prices': prices})
