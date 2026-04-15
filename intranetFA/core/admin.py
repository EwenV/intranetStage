from django.contrib import admin
from .models import Organigramme, RapportActivite


@admin.register(Organigramme)
class OrganigrammeAdmin(admin.ModelAdmin):
    readonly_fields = ("date_mise_a_jour", "fichier_avif")
    list_display = ("date_mise_a_jour", "fichier_pdf", "fichier_avif")


@admin.register(RapportActivite)
class RapportActiviteAdmin(admin.ModelAdmin):
    list_display = ("date", "fichier_pdf")
