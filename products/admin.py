from django.contrib import admin

from .models import Price, Product, Supermarket, Category, ProductReview, SupermarketReview

@admin.register(Supermarket)
class SupermarketAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'supermarket', 'amount', 'updated_at')
    list_filter = ('supermarket',)


@admin.register(ProductReview)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
   
@admin.register(SupermarketReview)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('supermarket', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
