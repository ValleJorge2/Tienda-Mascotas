from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import CartItem
from .serializers import CartItemSerializer
from orders.serializers import OrderSerializer
from core.permissions import IsOwnerOrAdmin
from products.models import Product

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        print(f"User: {self.request.user}")
        cart_items = CartItem.objects.filter(user=self.request.user)
        print(f"Cart items: {cart_items.count()}")
        for item in cart_items:
            print(f"Cart item: {item.id} - {item.product.name} - {item.quantity}")
        return cart_items

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        print(f"User: {request.user}")

        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                return Response(
                    {'error': f'Not enough stock. Available: {product.stock}, Requested: {quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product_id=product_id,
                defaults={'quantity': quantity}
            )

            if not created:
                # Update existing cart item
                new_quantity = cart_item.quantity + quantity
                if new_quantity > product.stock:
                    return Response(
                        {'error': f'Not enough stock. Available: {product.stock}, Total requested: {new_quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                cart_item.quantity = new_quantity
                cart_item.save()

            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        print(f"User: {request.user}")
        with transaction.atomic():
            # Get current cart items
            cart_items = self.get_queryset()

            if not cart_items.exists():
                return Response(
                    {'error': 'Your cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate shipping address
            shipping_address_id = request.data.get('shipping_address_id')
            if not shipping_address_id:
                return Response(
                    {'error': 'Shipping address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate stock for all items
            for item in cart_items:
                if item.product.stock < item.quantity:
                    return Response(
                        {
                            'error': f'Not enough stock for {item.product.name}. '
                            f'Available: {item.product.stock}, '
                            f'In cart: {item.quantity}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Calculate total amount
            total_amount = sum(item.quantity * item.product.price for item in cart_items)

            # Prepare order data
            order_data = {
                'shipping_address_id': shipping_address_id,
                'total_amount': total_amount,
                'items': [
                    {
                        'product_id': item.product.id,
                        'quantity': item.quantity
                    } for item in cart_items
                ]
            }

            # Create order
            order_serializer = OrderSerializer(data=order_data, context={'request': request})
            order_serializer.is_valid(raise_exception=True)
            order = order_serializer.save(user=request.user)

            # Clear the cart items after the order is created
            cart_items.update(quantity=0)

            return Response({
                'message': 'Order created successfully',
                'order': order_serializer.data
            }, status=status.HTTP_201_CREATED)