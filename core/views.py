from django.http import HttpResponse 
from django.shortcuts import render
from products.models import Product, Category

def home(request):
    query = request.GET.get('q', '')
    search_by = request.GET.get('search_by', 'product')
    category_filter = request.GET.get('category', '')

    products = Product.objects.all()
    categories = Category.objects.all()

    if category_filter:
        products = products.filter(category__slug=category_filter)

    # 2. Aplicamos la búsqueda de texto si el usuario escribió algo
    if query:
        match search_by:
            case 'supermarket':
                products = products.filter(prices__supermarket__name__icontains=query).distinct()
            case _:
                products = products.filter(name__icontains=query)

    return render(
        request,
        "core/index.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "search_by": search_by,
            "category_filter": category_filter,
        }
    )