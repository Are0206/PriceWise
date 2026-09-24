from django.contrib import admin

from .models import Price, Product, Supermarket, Category, Review


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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
