from django.urls import path
from .views import MyInbox, GetMessages, SendMessages

urlpatterns = [
    path("my-messages/", MyInbox.as_view(), name="my-inbox"),
    path(
        "get-messages/<int:sender_id>/<int:receiver_id>/",
        GetMessages.as_view(),
        name="get-messages",
    ),
    path("send-messages/", SendMessages.as_view(), name="send-messages"),
]
