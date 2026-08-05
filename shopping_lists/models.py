from django.db import models
from products.models import Product
# Create your models here.
class ShoppingList(models.Model):
    
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    products = models.ManyToManyField(
        Product,
        through='ShoppingListItem',
        related_name='shopping_lists'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ShoppingListItem(models.Model):
    
    shopping_list = models.ForeignKey(
        ShoppingList,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,   
        related_name='list_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [['shopping_list', 'product']]

    def __str__(self):
        return f"{self.quantity} x {self.product}"
