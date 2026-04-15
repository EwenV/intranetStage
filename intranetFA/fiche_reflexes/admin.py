from django.contrib import admin
from .models import FicheReflexes


@admin.register(FicheReflexes)
class FicheReflexesAdmin(admin.ModelAdmin):
    readonly_fields = ("date_ajout", "fichier_avif")
    list_display = ("titre", "date_ajout", "fichier_pdf", "fichier_avif")
