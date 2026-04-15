from django.urls import path

from . import views

app_name = "fiche_reflexes"
urlpatterns = [
    path("", views.fiche_reflexes_index_view, name="fiche_reflexes_index"),
    path("<int:pk>/", views.fiche_reflexes_view, name="fiche_reflexes"),
    path("aleatoire/", views.fiche_aleatoire_redirect, name="fiche_aleatoire"),
]
