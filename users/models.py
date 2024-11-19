from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
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
