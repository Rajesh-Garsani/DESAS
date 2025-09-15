from django.urls import path
from . import views

urlpatterns = [
    path('register/event-registrar/', views.register_event_registrar, name='register_event_registrar'),
    path('register/security-guard/', views.register_security_guard, name='register_security_guard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]