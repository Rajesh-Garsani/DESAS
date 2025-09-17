from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dashboard/', views.guard_dashboard, name='guard_dashboard'),
    path('id-card/view/', views.view_id_card, name='view_id_card'),
    path('id-card/download/', views.download_id_card, name='download_id_card'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('assignments/', views.assignments, name='assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('manage/', views.manage_guards, name='manage_guards'),
    path("assignments/<int:assignment_id>/reject/", views.reject_assignment, name="reject_assignment"),
    path("assignments/<int:assignment_id>/complete/", views.complete_assignment, name="complete_assignment"),
    path('assign-duty/', views.assign_duty, name='assign_duty'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('messages-log/', views.messages_log, name='messages_log'),
    path("history/", views.guard_history, name="guard_history"),
    path("history/pdf/", views.export_guard_history_pdf, name="export_guard_history_pdf"),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)