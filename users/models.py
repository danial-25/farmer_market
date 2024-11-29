from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User
from products.models import *
from django.core.mail import send_mail
import farmer_market_backend
from products.models import Product
from django.utils import timezone

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("farmer", "Farmer"),
        ("buyer", "Buyer"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="buyer")

    @property
    def is_farmer(self):
        return self.role == "farmer"

    @property
    def is_buyer(self):
        return self.role == "buyer"

    @property
    def is_admin(self):
        return self.role == "admin"


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

class DeliveryOption(models.Model):
    OPTION_TYPES = [
        ('HOME_DELIVERY', 'Home Delivery'),
        ('PICKUP_POINT', 'Pickup Point'),
        ('THIRD_PARTY', 'Third-Party Delivery'),
    ]

    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="delivery_options")
    option_type = models.CharField(max_length=50, choices=OPTION_TYPES)
    details = models.TextField(blank=True, null=True)  # Additional info, e.g., pickup location

    def __str__(self):
        return f"{self.farmer.username} - {self.get_option_type_display()}"

class Order(models.Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_details = models.TextField()  # Capture delivery address or special instructions
    delivery_option = models.ForeignKey(DeliveryOption, on_delete=models.SET_NULL, null=True, related_name="orders")
    is_completed = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True)

    class OrderStatus(models.TextChoices):
        PLACED = 'Placed', 'Placed'
        PROCESSED = 'Processed', 'Processed'
        SHIPPED = 'Shipped', 'Shipped'
        DELIVERED = 'Delivered', 'Delivered'
        CANCELLED = 'Cancelled', 'Cancelled'


    status = models.CharField(max_length=50, choices=OrderStatus.choices, default=OrderStatus.PLACED)
    # other fields as needed
    def change_status(self, new_status):
        if new_status != self.status:
            self.status = new_status
            self.save()

    def __str__(self):
        return f"Order {self.id} - {self.status}"

    def calculate_total(self):
        total = sum(item.get_subtotal() for item in self.items.all())
        return total

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def get_subtotal(self):
        return self.product.price * self.quantity