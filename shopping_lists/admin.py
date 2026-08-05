from django.contrib import admin
from .models import ShoppingList, ShoppingListItem
# Register your models here.

class ShoppingListItemInline(admin.TabularInline):
    model = ShoppingListItem
    extra = 1


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    inlines = [ShoppingListItemInline]