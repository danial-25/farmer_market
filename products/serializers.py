from .models import Farmer
from django.urls import reverse
from rest_framework.reverse import reverse
from rest_framework import serializers
from .models import Product, Category, ProductImage
from django.core.exceptions import ValidationError


class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ["id", "name", "location", "contact_info"]


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
        """Handle image resizing and creation."""
        images_data = validated_data.pop('images', [])
        product = Product.objects.create(**validated_data)

        for image in images_data:
            # Create ProductImage instances and link to product
            product_image = ProductImage(image=image)
            try:
                product_image.clean()  # Validate the image (size, format)
                product_image.save()   # Resize and save the image
                product.images.add(product_image)  # Add image to the product
            except ValidationError as e:
                raise serializers.ValidationError(str(e))

        return product
