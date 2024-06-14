from django.urls import path
from . import views

app_name = "ais"
urlpatterns = [path("process", views.process, name="process")]
