from django.http import HttpResponse 
from django.shortcuts import render
from products.models import Product

def home(request):
    query = request.GET.get('q', '')
    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    return render(
        request,
        "core/index.html",
        {
            "products": products,
            "query": query
        }
    )