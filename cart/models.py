from django.db import models
from users.models import User
from marketplace.models import Product

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    class Meta:
        verbose_name="Cart"
        verbose_name_plural="Carts"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_model} in {self.cart.user.username}'s cart"
    
    class Meta:
        verbose_name="Cart Item"
        verbose_name_plural="Cart Items"
