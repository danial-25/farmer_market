from rest_framework import serializers
from .models import Farmer, Category, Product
from django.urls import reverse
from rest_framework.reverse import reverse
from users.models import *


class FarmerSerializer(serializers.ModelSerializer):
    user = serializers.DictField(write_only=True)

    class Meta:
        model = Farmer
        fields = ["id", "name", "location", "contact_info", "user"]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = CustomUser.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            role="farmer",
        )
        buyer = Farmer.objects.create(user=user, **validated_data)
        return buyer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    farmer = FarmerSerializer(read_only=True)  # Embed Farmer details
    category = serializers.StringRelatedField()  # Show category name
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    # url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance):
        request = self.context.get("request")
        url = reverse(
            "products-detail",
            kwargs={"id": instance.id},
            request=request,
        )  # url to the instance
        representation = super().to_representation(instance)
        representation["url"] = url
        return representation


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "quantity_available",
            "category",
            "images",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not hasattr(request.user, "farmer"):
            raise serializers.ValidationError("Only farmers can create products.")

        farmer = request.user.farmer
        return Product.objects.create(farmer=farmer, **validated_data)
