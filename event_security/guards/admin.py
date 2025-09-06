from django.contrib import admin
from .models import SecurityGuardProfile, DutyAssignment

@admin.register(SecurityGuardProfile)
class SecurityGuardProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'guard_type', 'cnic', 'age', 'experience', 'is_approved')
    list_filter = ('guard_type', 'is_approved')
    search_fields = ('user__username', 'cnic')

@admin.register(DutyAssignment)
class DutyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('event', 'guard', 'assignment_date')
    list_filter = ('event__status', 'assignment_date')
    search_fields = ('event__name', 'guard__username')