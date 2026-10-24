from django.conf import settings
from django.db import models

class Supermarket(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    nutritional_info = models.TextField(blank=True, null=True) # RF-33: Información nutricional.
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )
    def get_cheapest_price(self): #RF-32
        return self.prices.select_related('supermarket').order_by('amount').first()
    
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
        help_text="Fecha del precio reportada por la fuente (campo 'Fecha' de la API).",
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

    def __str__(self):
        return f"{self.user.username} rated {self.supermarket.name}: {self.rating}"