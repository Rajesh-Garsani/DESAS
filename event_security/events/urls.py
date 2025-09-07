from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_event, name='add_event'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('manage/', views.manage_events, name='manage_events'),
    path('<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('<int:event_id>/reject/', views.reject_event, name='reject_event'),
    path("event/<int:event_id>/review/", views.add_review, name="add_review"),
    path("reviews/", views.review_list, name="review_list"),
]