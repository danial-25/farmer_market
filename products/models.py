from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Farmer(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        return self.name


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
    popularity = models.PositiveIntegerField(
        default=0
    )  # To enable sorting by popularity
    date_added = models.DateTimeField(auto_now_add=True)
    images = models.ImageField(upload_to="product_images/", null=True, blank=True)

    def __str__(self):
        return self.name
