# orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:pk>/cancel/', OrderViewSet.as_view({
        'post': 'cancel'
    }), name='order-cancel'),
]