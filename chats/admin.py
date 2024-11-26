from django.contrib import admin
from .models import ChatMessage


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'message', 'is_read', 'date']
    list_filter = ['is_read']
    search_fields = ['sender__username', 'receiver__username', 'message']


admin.site.register(ChatMessage, ChatMessageAdmin)
