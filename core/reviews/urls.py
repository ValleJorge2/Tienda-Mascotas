#reviews/urls.py
from django.urls import path
from .views import ReviewViewSet

urlpatterns = [
    path('products/<int:product_id>/reviews/', ReviewViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='product-reviews'),
    path('products/<int:product_id>/reviews/<int:pk>/', ReviewViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='review-detail'),
]