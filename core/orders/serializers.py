from .models import Order, OrderItem
from rest_framework import serializers
from products.serializers import Product, ProductSerializer
from users.serializers import ShippingAddress, ShippingAddressSerializer, UserSerializer
from cart.models import CartItem
from django.db import transaction
from rest_framework.exceptions import ValidationError

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price', 'created_at']
        read_only_fields = ['created_at', 'price']
    
    def validate(self, data):
        product = data['product']
        quantity = data['quantity']
        
        if product.stock < quantity:
            raise ValidationError({
                'quantity': f'Not enough stock. Available: {product.stock}, Requested: {quantity}'
            })
        
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all(),
        write_only=True,
        source='shipping_address'
    )
    user = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'status', 'payment_status',
                 'shipping_address', 'shipping_address_id', 'payment_details',
                 'tracking_number', 'notes', 'items', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_items(self, items_data):
        # Validate that all items have sufficient stock
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            if product.stock < quantity:
                raise ValidationError(
                    f'Product "{product.name}" does not have enough stock. '
                    f'Available: {product.stock}, Requested: {quantity}'
                )
        
        return items_data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Create the order first
        order = Order.objects.create(**validated_data)
        
        total_amount = 0
        created_items = []
        
        try:
            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                price = product.price
                
                # Check stock one more time within the transaction
                if product.stock < quantity:
                    raise ValidationError(
                        f'Product "{product.name}" does not have enough stock. '
                        f'Available: {product.stock}, Requested: {quantity}'
                    )
                
                # Create order item
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                created_items.append(order_item)
                
                # Update product stock
                product.stock -= quantity
                product.save()
                
                total_amount += price * quantity
            
            order.total_amount = total_amount
            order.save()
            
            # Clear the cart items after creating the order
            CartItem.objects.filter(user=order.user).delete()
            
            return order
            
        except Exception as e:
            # If anything goes wrong, delete the order and all created items
            order.delete()
            raise e