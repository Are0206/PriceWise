from .models import ShoppingList


def my_shopping_lists(request):
    """The logged-in user's lists, for the quick 'add to list' menu on product cards.

    The queryset is lazy: it only hits the database on pages that render the menu.
    """
    if not request.user.is_authenticated:
        return {'my_shopping_lists': []}
    return {'my_shopping_lists': ShoppingList.objects.filter(owner=request.user).order_by('-updated_at')}
