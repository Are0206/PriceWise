from django.contrib import admin

from .models import Price, Product, Supermarket, Category


@admin.register(Supermarket)
class SupermarketAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Category)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'supermarket', 'amount', 'updated_at')
    list_filter = ('supermarket',)
