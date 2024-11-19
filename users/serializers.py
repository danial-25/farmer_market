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

class BuyerSerializer(serializers.ModelSerializer):
    user = serializers.DictField(write_only=True)  # Expect a dictionary for user data

    class Meta:
        model = Buyer
        fields = ['id', 'delivery_address', 'contact_number', 'user']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = CustomUser.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            role='buyer',
        )
        buyer = Buyer.objects.create(user=user, **validated_data)
        return buyer
