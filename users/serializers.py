# from rest_framework import serializers
# from .models import *
# class BuyerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Buyer
#         fields = ('id', 'user', 'delivery_address', 'contact_number')

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

from rest_framework import serializers
from .models import Buyer
from users.models import CustomUser

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
