"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="E-commerce API",
      default_version='v1',
      description="API documentation for the E-commerce microservices",
      terms_of_service="https://www.yourapp.com/terms/",
      contact=openapi.Contact(email="contact@yourapp.com"),
      license=openapi.License(name="Your License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
   url='http://your-api-gateway-url/',  # Replace with your Kong gateway URL
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API Documentation endpoint
    path('api/endpoints/', include('endpoints.urls')),
    
    # Main API endpoints grouped by app
    path('api/v1/', include([
        # User management endpoints
        path('', include('users.urls')),
        
        # Core feature endpoints
        path('products/', include('products.urls')),
        path('categories/', include('categories.urls')),
        path('cart/', include('cart.urls')),
        path('orders/', include('orders.urls')),
        path('reviews/', include('reviews.urls')),
    ])),

     # Swagger/OpenAPI documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


"""
Django==5.1.3
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.6.0
django-filter==24.3
psycopg2-binary==2.9.10
python-dotenv==1.0.0
pika==1.3.1
requests==2.32.3
PyJWT==2.9.0
"""