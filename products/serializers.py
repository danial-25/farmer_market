from .models import Farmer
from django.urls import reverse
from rest_framework.reverse import reverse
from users.models import *
from rest_framework import serializers
from .models import Product, Category, ProductImage
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
import random
import os

from rest_framework import serializers
from .models import Farm


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ["name", "size", "address", "resources"]


class FarmerSerializer(serializers.ModelSerializer):
    user = serializers.DictField(write_only=True)
    # user = serializers.JSONField(write_only=True)
    class Meta:
        model = Farmer
        fields = ["id", "name", "location", "contact_info", "profile_picture", "user"]

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

    def update(self, instance, validated_data):
        # Update only Farmer-specific fields (do not touch user-related fields)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()  # Save the updated instance
        return instance
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = instance.user.id if instance.user else None  
        return representation



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


# class ProductCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = [
#             "name",
#             "description",
#             "price",
#             "quantity_available",
#             "category",
#             "images",
#             "popularity",  # Include popularity in the fields
#             "farmer",  # Include farmer in the fields (though this will be set in the view)
#         ]
#         read_only_fields = ["farmer"]  # Make sure 'farmer' is read-only

#     def create(self, validated_data):
#         """Handle image resizing, farmer assignment, and product creation."""
#         images_data = validated_data.pop("images", [])
#         # Extract the farmer from the user who is making the request
#         user = self.context["request"].user
#         farmer = (
#             user.farmer_profile
#         )  # Assuming you have a relationship between User and Farmer

#         # Add the farmer to the validated data
#         validated_data["farmer"] = farmer
#         product = Product.objects.create(**validated_data)
#         image_instances = []
#         for image in images_data:
#             # Create ProductImage instances and link to product
#             if isinstance(image, bytes):
#                 # Create a ContentFile with raw bytes
#                 image_name = "uploaded_image.jpg"  # You can use a default name or generate a unique name
#                 image = ContentFile(image, name=image_name)  # Assign a name here
#                 image_instances.append(product_image)
#             # Create ProductImage instance
#             product_image = ProductImage(image=image)
#             try:
#                 product_image.clean()  # Validate the image (size, format)
#                 product_image.save()  # Resize and save the image
#                 # product.images.add(product_image)  # Add image to the product
#                 product.images.set(image_instances)
#             except ValidationError as e:
#                 raise serializers.ValidationError(str(e))

#         return product


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "quantity_available",
            "category",
            "image",
            "popularity",
            "farmer",  # Include farmer in the fields (though this will be set in the view)
        ]
        read_only_fields = ["farmer", "popularity"]  # Make sure 'farmer' is read-only

    def create(self, validated_data):
        """Handle image resizing, farmer assignment, and product creation."""
        images_data = validated_data.pop("images", [])

        # Extract the farmer from the user who is making the request
        user = self.context["request"].user
        farmer = (
            user.farmer_profile
        )  # Assuming you have a relationship between User and Farmer

        # Add the farmer to the validated data
        validated_data["farmer"] = farmer
        validated_data["popularity"] = random.randint(1, 100)

        product = Product.objects.create(**validated_data)

        # Resize the image
        if validated_data.get("image"):
            resized_image = product.resize_image(validated_data["image"])
            product.image = resized_image  # Assign resized image to the product

        product.save()  # Save product with resized image
        return product

    # def update(self, instance, validated_data):
    #     """Handle partial updates of the product."""
    #     # Iterate over the validated data and update the corresponding fields
    #     for attr, value in validated_data.items():
    #         if attr == "image" and value:  # Handle image resizing if image is updated
    #             resized_image = instance.resize_image(value)
    #             setattr(instance, attr, resized_image)
    #         else:
    #             setattr(instance, attr, value)

    #     instance.save()  # Save the updated instance
    #     return instance

    def update(self, instance, validated_data):
        """Handle partial updates of the product."""
        image = validated_data.get("image", None)

        # Check if image is None or not provided

        # If we want to check if the current image exists on disk:
        if instance.image and not os.path.exists(instance.image.path):
            # If the current image does not exist, set image to None
            instance.image = None

        # Update other fields as usual
        for attr, value in validated_data.items():
            if attr != "image":
                setattr(instance, attr, value)

        instance.save()
        return instance

        # print("lol")
        # # Create the product
        # product = Product.objects.create(**validated_data)

        # # Create ProductImage instances and link them to the product
        # image_instances = []
        # for image in images_data:
        #     if isinstance(image, InMemoryUploadedFile):
        #         # Create a new ProductImage instance for each image
        #         # product_image = ProductImage(image=image)
        #         try:
        #             product.clean()  # Validate the image (size, format)
        #             product.save()  # Save the image and generate the file
        #             # image_instances.append(
        #             #     product_image
        #             # )  # Add the ProductImage instance to the list
        #         except ValidationError as e:
        #             raise serializers.ValidationError(str(e))

        # # Associate the image instances with the product
        # # product.images.set(image_instances)  # Many-to-many relationship assignment
        # return product
