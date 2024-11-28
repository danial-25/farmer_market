from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import hashlib
from django.core.files.base import ContentFile




class Farmer(models.Model):
    user = models.OneToOneField(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="farmer_profile",
        null=True,  # Allow null values temporarily
    )
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    contact_info = models.TextField()
    is_pending = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", default="profile_pictures/image.png"
    )


class Farm(models.Model):
    name = models.CharField(max_length=255)
    size = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., 123.45 acres
    address = models.TextField()
    farmer = models.OneToOneField(Farmer, on_delete=models.CASCADE, related_name="farm")
    resources = models.JSONField(
        blank=True, null=True
    )  # Example: {"seeds": 50, "tractors": 1}

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    image = models.ImageField(upload_to="product_images/")


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    popularity = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    # is_active = models.BooleanField(default=True)
    quantity_available = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    farmer = models.ForeignKey(
        Farmer, on_delete=models.CASCADE, related_name="products"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    # images = models.JSONField(default=list)
    # images = models.ManyToManyField(ProductImage, blank=True)

    pid = models.CharField(max_length=64, editable=False, null=True)

    def generate_pid(self):
        """Generate a consistent hash for core product attributes."""
        unique_string = f"{self.name}-{self.description}-{self.category}"
        return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        """Ensure the pid is generated before saving."""
        if not self.pid:
            self.pid = self.generate_pid()
        super().save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        """Ensure the pid is generated before saving and resize image."""
        if not self.pid:
            self.pid = self.generate_pid()

        # Resize image before saving
        if self.image:
            self.image = self.resize_image(self.image)

        super().save(*args, **kwargs)

    def resize_image(self, image):
        """Resize image to fit the required size and convert to RGB if necessary."""
        img = Image.open(image)

        # If the image has an alpha channel (RGBA), convert it to RGB
        if img.mode == "RGBA":
            img = img.convert("RGB")

        # Resize image to fit within 800x800
        img.thumbnail((800, 800))  # Resize to max 800x800

        # Save resized image to a BytesIO stream
        output = BytesIO()
        img.save(output, format="JPEG")
        output.seek(0)

        # Create and return InMemoryUploadedFile for resized image
        return InMemoryUploadedFile(
            output, "ImageField", image.name, "image/jpeg", output.tell(), None
        )


def resize_image(image, max_size=(800, 800)):
    """Resize the image to the specified size."""
    img = Image.open(image)
    img.thumbnail(max_size)

    output = BytesIO()
    img.save(output, format="JPEG")
    output.seek(0)

    return InMemoryUploadedFile(
        output, "ImageField", image.name, "image/jpeg", output.tell(), None
    )


# class ProductImage(models.Model):
#     image = models.ImageField(upload_to="product_images/")

#     def clean(self):
#         """Validate the image file."""
#         print(self.image.name)
#         if not self.image.name.lower().endswith((".png", ".jpg", ".jpeg")):
#             raise ValidationError("Only PNG, JPG, and JPEG image formats are allowed.")
#         if self.image.size > 5 * 1024 * 1024:  # 5MB limit
#             raise ValidationError("Image size must be less than 5MB.")

#     def save(self, *args, **kwargs):
#         """Resize image before saving."""
#         if self.image:
#             self.image = resize_image(self.image)
#         super().save(*args, **kwargs)


# class ProductImage(models.Model):
#     image = models.ImageField(upload_to="product_images/")

#     def clean(self):
#         """Validate the image file."""
#         # If the image is passed as bytes, convert it into a file object
#         if isinstance(self.image, bytes):
#             self.image = ContentFile(self.image)
#         print(self.image.size)
#         if hasattr(self.image, "name"):
#             # Validate file extension
#             if not self.image.name.lower().endswith((".png", ".jpg", ".jpeg")):
#                 raise ValidationError(
#                     "Only PNG, JPG, and JPEG image formats are allowed."
#                 )

#             # Validate image size (5MB limit)
#             if self.image.size > 5 * 1024 * 1024:  # 5MB limit
#                 raise ValidationError("Image size must be less than 5MB.")
#         else:
#             raise ValidationError("Invalid image format.")

#     def save(self, *args, **kwargs):
#         """Resize image before saving."""
#         if isinstance(self.image, BytesIO):
#             # Here you can use PIL or any other resizing logic if necessary
#             self.image = resize_image(self.image)
#         super().save(*args, **kwargs)
