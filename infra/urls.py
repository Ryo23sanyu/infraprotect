from django.urls import path
from . import views

app_name    = "infra"
urlpatterns = [
    path("", views.index, name="index"),
]