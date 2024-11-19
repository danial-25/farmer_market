from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User

import farmer_market_backend


# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES,default='buyer')
    # is_approved = models.BooleanField(default=False)
    # groups = models.ManyToManyField(
    #     Group,
    #     related_name="customuser_set",  # Change the related_name
    #     blank=True,
    # )
    # user_permissions = models.ManyToManyField(
    #     Permission,
    #     related_name="customuser_set",  # Change the related_name
    #     blank=True,
    # )

class Buyer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="buyer_profile")
    delivery_address = models.TextField()
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username} (Buyer)"

class Farmer(models.Model):
    user = models.OneToOneField(farmer_market_backend.settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    farm_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    pending_approval = models.BooleanField(default=True)

    def __str__(self):
        return self.name