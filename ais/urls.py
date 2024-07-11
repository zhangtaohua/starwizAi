from django.urls import path

from . import views

app_name = "ais"
urlpatterns = [path("health", views.health, name="health"), path("process", views.process, name="process")]
