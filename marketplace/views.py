from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from marketplace.models import Product
from marketplace.serializers import ProductSerializer
from marketplace.permissions import IsAdminOrSeller
from users.security.custom_jwt_auth import CustomJWTAuthentication

class ProductListCreateAPIView(APIView):
    """
    Handles listing and creating products.
    - Admins: Can list and create any product.
    - Sellers: Can list and create their own products.
    - Users: Can only view products.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSeller]
    authentication_classes=[CustomJWTAuthentication]

    def get(self, request):
        products = Product.objects.filter(is_available=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.is_staff or request.user.role=="Seller": 
            data = request.data.copy()   
            data["product_provider"] = request.user.id  
            serializer = ProductSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)


class ProductDetailAPIView(APIView):
    """
    Handles retrieving, updating, and deleting a product.
    - Admins: Can manage all products.
    - Sellers: Can manage only their own products.
    - Users: Can only view products.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSeller]
    authentication_classes=[CustomJWTAuthentication]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_available=True)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if request.user.is_staff or product.product_provider == request.user:
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if request.user.is_staff or product.product_provider == request.user:
            product.delete()
            return Response({"detail": "Product deleted."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
