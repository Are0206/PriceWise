from django.http import HttpResponse 
from django.shortcuts import render
from products.models import Product

def home(request):
    query = request.GET.get('q', '')
    search_by = request.GET.get('search_by', 'product')
    products = Product.objects.all()

    if search_by == 'supermarket':
            # Si supermercado es un campo ForeignKey/Relación en Product:
            products = products.filter(prices__supermarket__name__icontains=query).distinct()
            
            # NOTA: Si el campo en tu modelo se llama diferente (ej: 'store' o 'supermarket' de texto directo):
            # Usa 'supermarket__icontains=query' en su lugar.
    else:
            products = products.filter(name__icontains=query)

    return render(
        request,
        "core/index.html",
        {
            "products": products,
            "query": query,
            "search_by": search_by,
        }
    )