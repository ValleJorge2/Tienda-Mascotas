# products/serializers.py
from .models import Product
from rest_framework import serializers
from categories.serializers import Category, CategorySerializer

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 
            'category', 'category_id', 'animal_type', 
            'stock', 'specifications', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value