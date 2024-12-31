# cart/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('items/', CartViewSet.as_view({
        'post': 'add_item',
    }), name='cart-add-item'),
    path('items/<int:pk>/', CartViewSet.as_view({
        'put': 'update_item',
        'delete': 'remove_item',
    }), name='cart-item-detail'),
]
