from django.conf import settings
from django.db import models

class Supermarket(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # RF-40: ID of the store in the Los Precios API, so imports update instead of duplicating.
    api_id = models.PositiveIntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


# RF-44: sedes físicas de un supermercado.
class SupermarketLocation(models.Model):
    """Una sede de un supermercado. Un supermercado tiene muchas sedes."""

    supermarket = models.ForeignKey(
        Supermarket,
        on_delete=models.CASCADE,
        related_name="locations",
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre de la sede, por ejemplo: Éxito Colombia. Opcional.",
    )
    address = models.CharField(
        max_length=200,
        help_text="Dirección de la sede, por ejemplo: Calle 10 #43-25, El Poblado.",
    )

    class Meta:
        verbose_name = "Supermarket location"
        verbose_name_plural = "Supermarket locations"
        ordering = ["supermarket__name", "name", "address"]
        constraints = [
            models.UniqueConstraint(
                fields=["supermarket", "address"],
                name="unique_address_per_supermarket",
            ),
        ]

    def __str__(self):
        return f"{self.supermarket.name} - {self.name or self.address}"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='products/category_icons/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    # PROTECT: deleting a category must not silently delete its products, prices and reviews.
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    description = models.TextField(blank=True)
    nutritional_info = models.TextField(blank=True, null=True) # RF-33: Información nutricional.
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )
    # RF-40: data from the Los Precios API. The image URL is used when no image was uploaded.
    api_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    @property
    def photo_url(self):
        """An uploaded image wins; otherwise the photo URL imported from the API (RF-40)."""
        return self.image.url if self.image else self.image_url

    def get_cheapest_price(self): #RF-32
        """Lowest price; ties go to the oldest price row (lowest pk).

        Uses prices loaded with prefetch_related('prices') when a view provides
        them, so a page of product cards does not run one query per card.
        """
        prefetched = getattr(self, '_prefetched_objects_cache', {}).get('prices')
        if prefetched is not None:
            return min(prefetched, key=lambda price: (price.amount, price.pk), default=None)
        return self.prices.select_related('supermarket').order_by('amount', 'pk').first()
    
    def __str__(self):
        return self.name


class Price(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    supermarket = models.ForeignKey(Supermarket, on_delete=models.CASCADE, related_name='prices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'supermarket')

    def __str__(self):
        return f"{self.product.name} @ {self.supermarket.name}: {self.amount}"

class PriceHistory(models.Model):
    """Observación de precio. Solo de inserción: nunca se edita."""

    price = models.ForeignKey(
        Price,
        on_delete=models.CASCADE,
        related_name="history",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    price_date = models.DateField(
        help_text="Día en que se registró el precio (fecha local de la sincronización).",
    )
    captured_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento en que el pipeline guardó esta observación.",
    )

    class Meta:
        verbose_name = "Price history"
        verbose_name_plural = "Price history"
        ordering = ["-price_date", "-captured_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["price", "price_date"],
                name="unique_price_observation_per_date",
            ),
        ]
        indexes = [
            models.Index(fields=["price", "-price_date"]),
        ]

#RF-17: Modelo de productos favoritos

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# RF-30/RF-31: Modelo de reseñas de productos
class ProductReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name='productreview_rating_1_to_5',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.product.name}: {self.rating}"
    
# RF-34/RF-35: Modelo de reseñas de supermercados
class SupermarketReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supermarket_reviews'
    )
    supermarket = models.ForeignKey(
        Supermarket,
        on_delete=models.CASCADE,
        related_name='supermarket_reviews'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'supermarket')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name='supermarketreview_rating_1_to_5',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.supermarket.name}: {self.rating}"