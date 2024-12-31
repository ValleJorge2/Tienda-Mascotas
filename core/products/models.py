from django.db import models
from categories.models import Category


# products/models.py
class Product(models.Model):
    ANIMAL_TYPES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('fish', 'Fish'),
        ('small_pet', 'Small Pet'),
        ('other', 'Other')
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    animal_type = models.CharField(max_length=20, choices=ANIMAL_TYPES)
    stock = models.IntegerField(default=0)
    specifications = models.JSONField(default=dict, blank=True, null=True)  # Changed from djongo_models.JSONField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['animal_type']),
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f'{self.name} with {self.stock} and a price of {self.price} $'