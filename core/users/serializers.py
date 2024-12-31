# users/serializers.py
from rest_framework import serializers
from .models import ShippingAddress
from django.contrib.auth.models import User

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['id', 'street_address', 'city', 'state', 'postal_code', 
                 'country', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserSerializer(serializers.ModelSerializer):
    addresses = ShippingAddressSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'addresses']
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True}
        }