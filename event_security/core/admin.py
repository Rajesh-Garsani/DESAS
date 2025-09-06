from django.contrib import admin
from .models import MessageLog

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'method', 'status', 'sent_at')
    list_filter = ('method', 'status', 'sent_at')
    search_fields = ('recipient__username', 'content')
    readonly_fields = ('sent_at',)