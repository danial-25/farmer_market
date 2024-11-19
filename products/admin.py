from django.contrib import admin
from .models import Farmer


class FarmerAdmin(admin.ModelAdmin):
    # Fields to display in the list view of the Farmer model
    list_display = ("name", "location", "contact_info", "is_approved")
    list_filter = ("is_approved",)  # Filter by approval status
    search_fields = ("name", "location")  # Search by name or location

    # You can add custom methods for displaying fields if needed
    # Example for showing a user’s username in the list display
    def get_user_username(self, obj):
        return obj.user.username if obj.user else "No User"

    get_user_username.short_description = "Username"  # Column name


admin.site.register(Farmer, FarmerAdmin)
