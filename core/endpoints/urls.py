# endpoints/urls.py
from django.urls import path
from .views import EndpointListView

app_name = 'endpoints'

urlpatterns = [
    path('', EndpointListView.as_view(), name='endpoint-list'),
]