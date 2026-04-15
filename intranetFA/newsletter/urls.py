from django.urls import path

from . import views

app_name = "newsletter"
urlpatterns = [
    path("", views.index_view, name="index"),
    path("<int:pk>/", views.detail_view, name="detail"),
    path("outilsinternes", views.index_outil_view, name="index_outils_internes"),
    path(
        "outilsinternes/<int:pk>", views.detail_outil_view, name="detail_outil_interne"
    ),
]
