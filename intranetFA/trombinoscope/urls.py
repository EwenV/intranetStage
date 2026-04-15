from django.urls import path

from . import views

app_name = "trombinoscope"
urlpatterns = [
    path("", views.trombinoscope_view, name="trombinoscope"),
]
