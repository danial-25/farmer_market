from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from users.models import *
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


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
    is_active = models.BooleanField(default=True)
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

    low_stock_threshold = models.PositiveIntegerField(default=10)

    def is_low_stock(self):
        """Check if the product is below the low stock threshold."""
        return self.quantity_available <= self.low_stock_threshold

    def mark_out_of_stock(self):
        """Mark the product as out of stock."""
        self.quantity_available = 0
        self.save()

    def remove_from_marketplace(self):
        """Remove product from the marketplace (deactivate or delete)."""
        self.delete()


def resize_image(image, max_size=(800, 800)):
    """Resize the image to the specified size."""
    img = Image.open(image)
    img.thumbnail(max_size)

    output = BytesIO()
    img.save(output, format="JPEG")
    output.seek(0)

    return InMemoryUploadedFile(output, "ImageField", image.name, 'image/jpeg', output.tell(), None)


class ProductImage(models.Model):
    image = models.ImageField(upload_to="product_images/")
    def clean(self):
        """Validate the image file."""
        if not self.image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise ValidationError("Only PNG, JPG, and JPEG image formats are allowed.")
        if self.image.size > 5 * 1024 * 1024:  # 5MB limit
            raise ValidationError("Image size must be less than 5MB.")

    def save(self, *args, **kwargs):
        """Resize image before saving."""
        if self.image:
            self.image = resize_image(self.image)
        super().save(*args, **kwargs)