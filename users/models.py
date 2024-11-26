from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User
from products.models import *

import farmer_market_backend
from products.models import Product


# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("farmer", "Farmer"),
        ("buyer", "Buyer"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="buyer")


class Buyer(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="buyer_profile"
    )
    delivery_address = models.TextField()
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username} (Buyer)"


# class Farmer(models.Model):
#     user = models.OneToOneField(
#         farmer_market_backend.settings.AUTH_USER_MODEL, on_delete=models.CASCADE
#     )
#     name = models.CharField(max_length=255)
#     farm_name = models.CharField(max_length=255)
#     location = models.CharField(max_length=255)
#     phone_number = models.CharField(max_length=15)
#     pending_approval = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name

class Cart(models.Model):
    buyer = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return sum(item.total_price() for item in self.items.all())

    def total(self):
        tax_and_fees = 200  # Example fixed fee
        delivery_fee = 100  # Example fixed fee
        return self.subtotal() + tax_and_fees + delivery_fee

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.product.price  # Assuming Product has a `price` field
