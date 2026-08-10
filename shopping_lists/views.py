from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ShoppingListForm, ShoppingListItemFormSet
from .models import ShoppingList
from .services import calculate_estimated_savings, recommend_cheapest_supermarket
# Create your views here.

def shopping_list_create(request):
    
    if request.method == 'POST':
        form = ShoppingListForm(request.POST)
        formset = ShoppingListItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                shopping_list = form.save()
                formset.instance = shopping_list
                formset.save()
            return redirect('shopping_lists:detail', pk=shopping_list.pk)
    else:
        form = ShoppingListForm()
        formset = ShoppingListItemFormSet()

    return render(request, 'shopping_lists/form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create shopping list',
    })


def shopping_list_detail(request, pk):
    
    shopping_list = get_object_or_404(ShoppingList, pk=pk)
    savings = calculate_estimated_savings(shopping_list)
    cheapest_supermarket = recommend_cheapest_supermarket(shopping_list)
    return render(request, 'shopping_lists/detail.html', {
        'shopping_list': shopping_list,
        "savings": savings,
        "cheapest_supermarket": cheapest_supermarket,
    })


def shopping_list_index(request):
    
    shopping_lists = ShoppingList.objects.prefetch_related('items')
    return render(request, 'shopping_lists/index.html', {
        'shopping_lists': shopping_lists,
    })