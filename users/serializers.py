# from rest_framework import serializers
# from .models import *
# class BuyerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Buyer
#         fields = ('id', 'user', 'delivery_address', 'contact_number')
from requests import Response

#     def create(self, validated_data):
#         user_data = validated_data.pop('user')
#         user = CustomUser.objects.create_user(
#             username=user_data['username'],
#             email=user_data['email'],
#             password=user_data['password'],
#             role='buyer'
#         )
#         buyer = Buyer.objects.create(user=user, **validated_data)
#         return buyer

from rest_framework import serializers, status
from rest_framework.views import APIView

from .models import Buyer, OrderItem, Order
from users.models import CustomUser
from .models import Cart, CartItem

# from users.models import Farmer


class BuyerSerializer(serializers.ModelSerializer):
    user = serializers.DictField(write_only=True)  # Expect a dictionary for user data

    class Meta:
        model = Buyer
        fields = ["id", "delivery_address", "contact_number", "user"]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = CustomUser.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            role="buyer",
        )
        buyer = Buyer.objects.create(user=user, **validated_data)
        return buyer

    def update(self, instance, validated_data):
        # Update only Buyer-specific fields (do not touch user-related fields)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()  # Save the updated instance
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["user"] = instance.user.id if instance.user else None
        return representation


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2
    )

    class Meta:
        model = CartItem
        fields = ["id", "product_name", "product_price", "quantity", "total_price"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    subtotal = serializers.SerializerMethodField()
    tax_and_fees = serializers.SerializerMethodField()
    delivery_fee = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "subtotal",
            "tax_and_fees",
            "delivery_fee",
            "total",
            "created_at",
        ]

    def get_subtotal(self, obj):
        return obj.subtotal()

    def get_tax_and_fees(self, obj):
        return 200  # Example fixed fee

    def get_delivery_fee(self, obj):
        return 100  # Example fixed fee

    def get_total(self, obj):
        return obj.total()


class OrderItemSerializer(serializers.ModelSerializer):
    prices = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "prices"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "delivery_details",
            "items",
            "total_price",
            "is_completed",
            "order_date",
        ]
        read_only_fields = ["buyer", "total_price", "is_completed", "status"]

    def get_total_price(self, obj):
        return obj.calculate_total()

    def create(self, validated_data):
        # Access user from the context and safely create order
        user = self.context.get("request").user
        if not user:
            raise serializers.ValidationError("User not found in request context.")

        items_data = validated_data.pop("items")
        order = Order.objects.create(buyer=user, **validated_data)

        # Add order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Calculate total price
        order.calculate_total()
        return order


# class FarmerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Farmer
#         fields = ['id', 'user', 'name', 'farm_name', 'location', 'phone_number', 'pending_approval']
#         read_only_fields = ['id', 'pending_approval']

#     def create(self, validated_data):
#         # Custom creation logic if needed
#         return Farmer.objects.create(**validated_data)

#     def update(self, instance, validated_data):
#         # Custom update logic if needed
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         return instance
