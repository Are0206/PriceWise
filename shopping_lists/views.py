from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ShoppingListForm, ShoppingListItemFormSet
from .models import ShoppingList
from .services import *

#RF-1: Create shopping lists
def create_shopping_lists(request):
    
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


def shopping_list_edit(request, pk):
    
    shopping_list = get_object_or_404(ShoppingList, pk=pk)

    if request.method == 'POST':
        form = ShoppingListForm(request.POST, instance=shopping_list)
        formset = ShoppingListItemFormSet(request.POST, instance=shopping_list)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            return redirect('shopping_lists:detail', pk=shopping_list.pk)
    else:
        form = ShoppingListForm(instance=shopping_list)
        formset = ShoppingListItemFormSet(instance=shopping_list)

    return render(request, 'shopping_lists/form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit shopping list',
    })

#RF-5: Delete shopping lists
def delete_shopping_lists(request, pk):

    shopping_list = get_object_or_404(ShoppingList, pk=pk)

    if request.method == 'POST':
        shopping_list.delete()
        return redirect('shopping_lists:index')

    return render(request, 'shopping_lists/confirm_delete.html', {
        'shopping_list': shopping_list,
    })


def shopping_list_details(request, pk):
    
    shopping_list = get_object_or_404(ShoppingList, pk=pk)
    
    raw_breakdown = calculate_supermarket_breakdown(shopping_list)
    breakdown, best = get_cheapest_supermarket_recommendation(raw_breakdown) #RF-2
    savings = calculate_estimated_savings(breakdown) #RF-3

    return render(request, 'shopping_lists/detail.html', {
        'shopping_list': shopping_list,
        'breakdown': breakdown,
        'best': best,
        'savings': savings,
    })

def index(request):
    
    shopping_lists = ShoppingList.objects.prefetch_related('items')
    return render(request, 'shopping_lists/index.html', {
        'shopping_lists': shopping_lists,
    })