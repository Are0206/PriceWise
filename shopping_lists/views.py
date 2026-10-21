from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import ShoppingListForm, ShoppingListItemFormSet
from .models import ShoppingList, ShoppingListItem
from .services import *

def index(request):
    shopping_lists = []
    if request.user.is_authenticated:
        shopping_lists = ShoppingList.objects.filter(owner=request.user).prefetch_related('items')
    return render(request, 'shopping_lists/index.html', {
        'shopping_lists': shopping_lists,
    })

#RF-1: Create shopping lists
@login_required
def create_shopping_lists(request):
    
    if request.method == 'POST':
        form = ShoppingListForm(request.POST)
        formset = ShoppingListItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                shopping_list = form.save(commit=False)
                shopping_list.owner = request.user
                shopping_list.save()
                formset.instance = shopping_list
                formset.save()
            return redirect('shopping_lists:detail', pk=shopping_list.pk)
    else:
        form = ShoppingListForm()
        formset = ShoppingListItemFormSet()

    return render(request, 'shopping_lists/form.html', {
        'form': form,
        'formset': formset,
        'title': 'Crear lista',
    })

#RF-4: Edit shopping lists
@login_required
def edit_shopping_lists(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, owner=request.user)

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
        'title': 'Editar lista',
    })

#RF-5: Delete shopping lists
@login_required
def delete_shopping_lists(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, owner=request.user)

    if request.method == 'POST':
        shopping_list.delete()
        messages.success(request, 'Lista borrada.')
        # The lists index is only the panel fragment, so go home with the panel open.
        return redirect(f"{reverse('index')}?open_lists=true")

    return render(request, 'shopping_lists/confirm_delete.html', {
        'shopping_list': shopping_list,
    })

#RF-37: Duplicate shopping lists
@login_required
def duplicate_shopping_lists(request, pk):
    original = get_object_or_404(ShoppingList, pk=pk, owner=request.user)

    if request.method != 'POST':
        return redirect('shopping_lists:detail', pk=original.pk)

    # ShoppingList uses a UUID primary key whose default is computed when the
    # instance is built, not when it is saved. Setting pk = None and saving
    # would leave it empty, so the copy is created explicitly.
    name_field = ShoppingList._meta.get_field('name')
    copy_name = f"{original.name} (copia)"[:name_field.max_length]

    with transaction.atomic():
        copy = ShoppingList.objects.create(name=copy_name, owner=request.user)
        ShoppingListItem.objects.bulk_create([
            ShoppingListItem(
                shopping_list=copy,
                product=item.product,
                quantity=item.quantity,
            )
            for item in original.items.all()
        ])

    return redirect('shopping_lists:detail', pk=copy.pk)

#RF-15: Share shopping lists (the link is read-only; only the owner can change the list)
@login_required
def share_shopping_lists(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, owner=request.user)
    share_url = request.build_absolute_uri(reverse('shopping_lists:detail', kwargs={'pk': shopping_list.pk}))

    return render(request, 'shopping_lists/share.html', {
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
        'is_owner': request.user.is_authenticated and shopping_list.owner_id == request.user.id,
    })