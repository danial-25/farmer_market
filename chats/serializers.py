from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_profile = serializers.SerializerMethodField()
    receiver_profile = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'sender',
            'receiver',
            'message',
            'is_read',
            'date',
            'sender_profile',
            'receiver_profile',
        ]

    def get_sender_profile(self, obj):
        if obj.sender.role == "buyer" and hasattr(obj.sender, "buyer_profile"):
            return {
                "id": obj.sender.buyer_profile.id,
                "delivery_address": obj.sender.buyer_profile.delivery_address,
                "contact_number": obj.sender.buyer_profile.contact_number,
            }
        elif obj.sender.role == "farmer" and hasattr(obj.sender, "farmer_profile"):
            return {
                "id": obj.sender.farmer_profile.id,
                "name": obj.sender.farmer_profile.name,
                "location": obj.sender.farmer_profile.location,
                "contact_info": obj.sender.farmer_profile.contact_info,
            }
        return None

    def get_receiver_profile(self, obj):
        if obj.receiver.role == "buyer" and hasattr(obj.receiver, "buyer_profile"):
            return {
                "id": obj.receiver.buyer_profile.id,
                "delivery_address": obj.receiver.buyer_profile.delivery_address,
                "contact_number": obj.receiver.buyer_profile.contact_number,
            }
        elif obj.receiver.role == "farmer" and hasattr(obj.receiver, "farmer_profile"):
            return {
                "id": obj.receiver.farmer_profile.id,
                "name": obj.receiver.farmer_profile.name,
                "location": obj.receiver.farmer_profile.location,
                "contact_info": obj.receiver.farmer_profile.contact_info,
            }
        return None
