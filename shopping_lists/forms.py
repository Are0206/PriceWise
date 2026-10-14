from django import forms
from django.forms import inlineformset_factory
from products.models import Product
from .models import ShoppingList, ShoppingListItem


class ShoppingListForm(forms.ModelForm):

    class Meta:
        model = ShoppingList
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ej.: Mercado de la semana',
                'class': 'form-input',
            })
        }
        labels = {'name': 'Nombre de la lista'}


class ShoppingListItemForm(forms.ModelForm):

    class Meta:
        model = ShoppingListItem
        fields = ['product', 'quantity']
        labels = {'product': 'Producto', 'quantity': 'Cantidad'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.order_by('name')


ShoppingListItemFormSet = inlineformset_factory(
    parent_model=ShoppingList,
    model=ShoppingListItem,
    form=ShoppingListItemForm,
    fields=['product', 'quantity'],
    extra=1,
    can_delete=True,
)