from rest_framework import generics, permissions
from django.db.models import Q
from .models import ChatMessage
from .serializers import ChatMessageSerializer


class MyInbox(generics.ListAPIView):
    """
    API view to list all messages for a specific user,
    retrieving only the last message for each chat.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # user_id = self.kwargs['user_id']  # Get 'user_id' from the URL
        user_id = self.request.user.id

        # Fetch last message in each chat where user is either sender or receiver
        messages = (
            ChatMessage.objects.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
            .order_by("sender_id", "receiver_id", "-id")
            .distinct("sender_id", "receiver_id")
        )
        return messages


class GetMessages(generics.ListAPIView):
    """
    API view to retrieve messages between two users.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        sender_id = self.kwargs["sender_id"]  # Get sender ID from the URL
        receiver_id = self.kwargs["receiver_id"]  # Get receiver ID from the URL

        return ChatMessage.objects.filter(
            Q(sender_id=sender_id, receiver_id=receiver_id)
            | Q(sender_id=receiver_id, receiver_id=sender_id)
        ).order_by(
            "date"
        )  # Order by the date of the messages


class SendMessages(generics.CreateAPIView):
    """
    API view to send a message between users.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
