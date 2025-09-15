from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.guard_dashboard, name='guard_dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('assignments/', views.assignments, name='assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('manage/', views.manage_guards, name='manage_guards'),
    path("assignments/<int:assignment_id>/reject/", views.reject_assignment, name="reject_assignment"),
    path("assignments/<int:assignment_id>/complete/", views.complete_assignment, name="complete_assignment"),
    path('assign-duty/', views.assign_duty, name='assign_duty'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('messages-log/', views.messages_log, name='messages_log'),
]