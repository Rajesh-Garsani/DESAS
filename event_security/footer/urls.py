from django.urls import path
from . import views

app_name = "footer"

urlpatterns = [
    path("page/<slug:slug>/", views.page_detail, name="page_detail"),
]
