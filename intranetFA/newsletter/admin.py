from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Article
from .models import OutilInterne
from django.urls import reverse
from django.utils.html import format_html


class BaseArticleAdmin(SummernoteModelAdmin):
    summernote_fields = ("contenu",)
    readonly_fields = ("date_derniere_publication", "date_creation", "auteur")
    search_fields = ("titre", "contenu", "auteur")
    list_filter = ("categorie", "est_publie")
    list_display = (
        "titre",
        "auteur",
        "categorie",
        "est_publie",
        "date_derniere_publication",
        "preview_link",
    )

    # Les utilisateurs non admin ne voient que leurs articles
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(auteur=request.user)

    # Autorisation d'édition seulement pour l'auteur ou l'admin
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.auteur == request.user or request.user.is_superuser

    # Autorisation de suppression seulement pour l'auteur ou l'admin
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.auteur == request.user or request.user.is_superuser

    # Lien de prévisualisation
    def preview_link(self, obj):
        url = reverse("newsletter:detail", args=[obj.pk])
        return format_html(
            '<a class="button" target="_blank" href="{}">Prévisualiser</a>', url
        )

    preview_link.short_description = "Aperçu"


@admin.register(Article)
class ArticleAdmin(BaseArticleAdmin):
    # Remplis le champ auteur
    def save_model(self, request, obj, form, change):
        if not change:
            obj.auteur = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """On exclu les outils internes de la liste des articles"""
        qs = super().get_queryset(request)
        return qs.filter(outilinterne__isnull=True)

    def get_form(self, request, obj=None, **kwargs):
        """Limite les choix de catégories selon les droits"""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            categories_autorisees = []
            if request.user.has_perm("newsletter.peut_ecrire_actu"):
                categories_autorisees.append("ACTU")
            if request.user.has_perm("newsletter.peut_ecrire_rpresse"):
                categories_autorisees.append("RPRESSE")
            if request.user.has_perm("newsletter.peut_ecrire_rh"):
                categories_autorisees.append("RH")
            if request.user.has_perm("newsletter.peut_ecrire_adm"):
                categories_autorisees.append("ADM")
            if request.user.has_perm("newsletter.peut_ecrire_outil"):
                categories_autorisees.append("OUTIL")
            if request.user.has_perm("newsletter.peut_ecrire_si"):
                categories_autorisees.append("SI")

            if "categorie" in form.base_fields and categories_autorisees:
                form.base_fields["categorie"].choices = [
                    (code, label)
                    for code, label in Article.CATEGORIES
                    if code in categories_autorisees
                ]

        return form

    def has_change_permission(self, request, obj=None):
        """On interdit l'édition si c'est un article lié à un OutilInterne"""
        if obj is None:
            return True
        if hasattr(obj, "outilinterne"):
            return False
        return obj.auteur == request.user or request.user.is_superuser


@admin.register(OutilInterne)
class OutilInterneAdmin(BaseArticleAdmin):
    summernote_fields = ("contenu",)
    readonly_fields = ("date_derniere_publication", "date_creation", "auteur")
    list_display = (
        "titre",
        "auteur",
        "lien_outil",
        "est_publie",
        "date_derniere_publication",
        "preview_link",
    )

    # Remplis les champs auteur et categorie
    def save_model(self, request, obj, form, change):
        if not change:
            obj.auteur = request.user
            obj.categorie = "OUTIL"  # Forcer la catégorie
        super().save_model(request, obj, form, change)

    # Empêche d’afficher ou modifier la catégorie dans le formulaire admin
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "categorie" in form.base_fields:
            form.base_fields["categorie"].disabled = True
            form.base_fields["categorie"].initial = "OUTIL"
        return form
