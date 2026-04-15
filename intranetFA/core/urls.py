from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    path("organigramme/", views.organigramme_view, name="organigramme"),
    path("rapport-activite/", views.rapport_activite_view, name="rapport_activite"),
]
