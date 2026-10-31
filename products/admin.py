from django.contrib import admin

from .models import (
    Price,
    Product,
    Supermarket,
    SupermarketLocation,
    Category,
    ProductReview,
    SupermarketReview,
)

# RF-44: permite cargar las sedes desde la misma página del supermercado.
class SupermarketLocationInline(admin.TabularInline):
    model = SupermarketLocation
    extra = 1


@admin.register(Supermarket)
class SupermarketAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_count')
    inlines = [SupermarketLocationInline]

    @admin.display(description='Sedes')
    def location_count(self, supermarket):
        return supermarket.locations.count()


@admin.register(SupermarketLocation)
class SupermarketLocationAdmin(admin.ModelAdmin):
    list_display = ('supermarket', 'name', 'address')
    list_filter = ('supermarket',)
    search_fields = ('name', 'address')


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
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
   
@admin.register(SupermarketReview)
class SupermarketReviewAdmin(admin.ModelAdmin):
    list_display = ('supermarket', 'user', 'rating', 'created_at')
    list_filter = ('rating',)