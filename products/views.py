from django.core.paginator import Paginator
from django.db.models import Count, Min
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Favorite, Category, Product, Supermarket, ProductReview, SupermarketReview
from .services import *

#RF-9: View product details
def view_product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cheapest_price = product.prices.select_related('supermarket').order_by('amount').first() #RF-32
    reviews = product.reviews.select_related('user')
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    return render(request, 'products/product_detail.html', {
        'product': product,
        'cheapest_price': cheapest_price, #RF-32
        'reviews': reviews,
        'user_review': user_review,
    })

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

    paginator = Paginator(products, 24)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    #RF-17
    user_favorite_ids = []
    if request.user.is_authenticated:
        user_favorite_ids = list(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    return render(
        request,
        "products/index.html",
        {
            "products": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "query_string": query_string,
            "categories": categories,
            "query": query,
            "search_by": search_by,
            "category_filter": category_filter,
            "min_price": min_price_raw,
            "max_price": max_price_raw,
            "sort": sort,
            "user_favorite_ids": user_favorite_ids,
        }
    )


#RF-17 Mark products as favorites
@login_required
def toggle_favorite(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)

        if not created:
            favorite.delete()

    # Go back to the page that sent the form, but never to another site.
    referer = request.META.get('HTTP_REFERER', '')
    if url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(referer)
    return redirect('/')


#RF-41: List favorite products
@login_required
def list_favorite_products(request):
    products = (
        Product.objects.filter(favorited_by__user=request.user)
        .order_by('-favorited_by__created_at')
    )
    return render(request, 'products/favorites.html', {
        'products': products,
        'user_favorite_ids': [product.id for product in products],
    })


#RF-30: Review products
@login_required
def submit_review(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        if rating in [str(n) for n in range(1, 6)]:
            ProductReview.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={'rating': rating, 'comment': comment},
            )

    return redirect('products:detail', pk=product.pk)

#RF-31: Delete product reviews
@login_required
def delete_review(request, review_id):
    review = get_object_or_404(ProductReview, pk=review_id, user=request.user)
    product_pk = review.product_id

    if request.method == 'POST':
        review.delete()

    return redirect('products:detail', pk=product_pk)

# Logo files in static/img/supermarkets/, keyed by supermarket name.
SUPERMARKET_LOGOS = {
    'D1': 'd1.webp',
    'Éxito': 'exito.webp',
    'Jumbo': 'jumbo.svg',
    'Carulla': 'carulla.jpeg',
}

def supermarkets_index(request):
    supermarkets = list(Supermarket.objects.annotate(
        price_count=Count('prices')
    ).prefetch_related('locations'))
    for supermarket in supermarkets:
        supermarket.logo = SUPERMARKET_LOGOS.get(supermarket.name)

    return render(request, 'supermarkets/index.html', {
        'supermarkets': supermarkets,
    })
    
def supermarkets_details(request, pk):
    supermarket = get_object_or_404(
        Supermarket.objects.prefetch_related('locations'), pk=pk
    )
    reviews = supermarket.supermarket_reviews.select_related('user')
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    return render(request, 'supermarkets/details.html', {
        'supermarket': supermarket,
        'reviews': reviews,
        'user_review': user_review,
    })

#RF-34: Review supermarkets
@login_required
def submit_supermarket_review(request, pk):
    supermarket = get_object_or_404(Supermarket, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        if rating in [str(n) for n in range(1, 6)]:
            SupermarketReview.objects.update_or_create(
                user=request.user,
                supermarket=supermarket,
                defaults={'rating': rating, 'comment': comment},
            )

    return redirect('products:supermarkets_details', pk=supermarket.pk)


#RF-35: Delete supermarkets reviews
@login_required
def delete_supermarket_review(request, review_id):
    review = get_object_or_404(SupermarketReview, pk=review_id, user=request.user)
    supermarket_pk = review.supermarket_id

    if request.method == 'POST':
        review.delete()

    return redirect('products:supermarkets_details', pk=supermarket_pk)
