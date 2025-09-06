from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'datetime', 'location', 'registrar', 'status')
    list_filter = ('event_type', 'status', 'datetime')
    search_fields = ('name', 'location', 'registrar__username')
    date_hierarchy = 'datetime'