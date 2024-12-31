# users/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import UserSerializer, ShippingAddressSerializer, ShippingAddress
from core.permissions import *
import datetime

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['register', 'login']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy', 'profile']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data.get('email', ''),
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', '')
        )
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        response = Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': access_token,
        }, status=status.HTTP_201_CREATED)
        
        # Set cookies for newly registered user
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=True,  # Set to False during development if not using HTTPS
            samesite='Lax',
            max_age=86400  # 1 day
        )
        
        response.set_cookie(
            'refresh_token',
            str(refresh),
            httponly=True,
            secure=True,  # Set to False during development if not using HTTPS
            samesite='Lax',
            max_age=604800  # 7 days
        )
        
        return response

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if username is None or password is None:
            return Response({
                'error': 'Please provide both username and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        response = Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': access_token,
        })
        
        # Set cookies with httponly flag
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=True,  # Set to False during development if not using HTTPS
            samesite='Lax',
            max_age=86400  # 1 day
        )
        
        response.set_cookie(
            'refresh_token',
            str(refresh),
            httponly=True,
            secure=True,  # Set to False during development if not using HTTPS
            samesite='Lax',
            max_age=604800  # 7 days
        )
        
        return response

    @action(detail=False, methods=['post'])
    def logout(self, request):
        response = Response({'message': 'Successfully logged out'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

    @action(detail=False, methods=['get', 'put'])
    def profile(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)