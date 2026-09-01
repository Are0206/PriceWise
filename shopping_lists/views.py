from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import ShoppingListForm, ShoppingListItemFormSet
from .models import ShoppingList
from .services import *

def index(request):
    
    shopping_lists = ShoppingList.objects.prefetch_related('items')
    return render(request, 'shopping_lists/index.html', {
        'shopping_lists': shopping_lists,
    })

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

#RF-4: Edit shopping lists
def edit_shopping_lists(request, pk):
    
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

#RF-15: Share shopping lists 
def share_shopping_lists(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk) 
    share_permission = request.GET.get('permission', 'read')
    
    if share_permission == 'edit':
        share_link = 'shopping_lists:edit'
    else:
        share_link = 'shopping_lists:detail'
    
    relative_url = reverse(share_link, kwargs={'pk': shopping_list.pk})
    base_url = request.build_absolute_uri(relative_url)
    share_url = f"{base_url}?permission={share_permission}"
    
    return render(request, 'shopping_lists/share.html', {
        'share_permission': share_permission,
        'shopping_list': shopping_list,
        'share_url': share_url,
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
