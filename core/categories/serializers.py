# categories/serializers.py
from .models import Category
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description','created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']