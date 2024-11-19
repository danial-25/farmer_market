from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from users.models import *


class Farmer(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="farmer_profile",
        null=True,  # Allow null values temporarily
    )
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    contact_info = models.TextField()
    is_approved = models.BooleanField(default=False)


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    popularity = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    quantity_available = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    farmer = models.ForeignKey(
        Farmer, on_delete=models.CASCADE, related_name="products"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    images = models.ImageField(upload_to="product_images/", null=True, blank=True)

    def is_low_stock(self):
        return self.quantity_available < 5

    def __str__(self):
        return self.name
