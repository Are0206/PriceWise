from django.db import models


class Supermarket(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

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
