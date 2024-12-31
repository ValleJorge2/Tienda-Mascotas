# cart/serializers.py
from .models import CartItem
from rest_framework import serializers
from products.serializers import Product, ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_total_price(self, obj):
        return obj.quantity * obj.product.price

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value