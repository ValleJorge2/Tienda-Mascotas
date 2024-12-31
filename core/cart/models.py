from django.db import models
from users.models import User
from products.models import Product

# cart/models.py
class CartItem(models.Model):
    user = models.ForeignKey(User, related_name='cart_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Changed from IntegerField to ensure positive values
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ['user', 'product']  # Prevent duplicate products in cart


    def __str__(self):
        return self.product