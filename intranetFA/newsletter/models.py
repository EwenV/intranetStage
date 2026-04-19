from django.db import models
from django.utils import timezone
from django_summernote.models import AbstractAttachment
import uuid
import os
from core.services.conversion_avif import ConversionAvifService
import logging
from django.conf import settings
import re
from core.services.validators import validate_url

logger = logging.getLogger("newsletter")


class Article(models.Model):
    CATEGORIES = [
        ("ACTU", "Actualité"),
        ("RPRESSE", "Revue de presse"),
        ("RH", "Info RH"),
        ("ADM", "Administration générale"),
        ("OUTIL", "Outil Interne"),
        ("SI", "Info SI"),
    ]

    titre = models.CharField(max_length=100)
    date_derniere_publication = models.DateField(null=True, blank=True, editable=False)
    date_creation = models.DateField(default=timezone.now, editable=False)
    contenu = models.TextField(default="", blank=True)
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False
    )
    est_publie = models.BooleanField(default=False)
    categorie = models.CharField(max_length=100, choices=CATEGORIES)
    image_en_tete = models.ImageField(upload_to="articles/", blank=True, null=True)

    def get_images_utilisees(self):
        """Retourne les images utilisées dans cet article"""
        if not self.contenu:
            return CustomAttachment.objects.none()

        import re

        # Trouve toutes les URLs d'images dans le contenu HTML
        img_urls = re.findall(r'/media/django-summernote/[^"\'>\s]+', self.contenu)

        # Extrait juste les noms de fichiers
        filenames = [url.split("/")[-1] for url in img_urls]

        if not filenames:
            return CustomAttachment.objects.none()

        # Recherche dans la DB
        pattern = "(" + "|".join(re.escape(f) for f in filenames) + ")$"
        return CustomAttachment.objects.filter(file__regex=pattern)

    def get_extrait(self):
        """créer l'extrait à partir de contenu, en prenant le premier paragraphe <p><\p> et en nettoyant les balises internes"""
        MAX_CHAR = 300
        contenu = self.contenu
        balise_o = "<p>"
        balise_f = "</p>"
        extrait = ""

        # On cherche les balises <p> avec ou sans attributs
        match = re.search(r"<p[^>]*>", contenu)
        if not match:
            logger.debug("Pas de <p> trouvé dans contenu")
            return ""

        # Trouve le premier paragraphe <p>
        start = match.end()  # Position après la balise ouvrante
        end = contenu.find("</p>", start)
        if end == -1:
            end = len(contenu)

        contenu = contenu[start:end]

        # Nettoie les balises HTML du premier paragraphe
        texte_nettoye = ""
        i = 0
        while i < len(contenu):
            if contenu[i] == "<":
                # Saute jusqu'à la fin de la balise
                while i < len(contenu) and contenu[i] != ">":
                    i += 1
                i += 1
            else:
                texte_nettoye += contenu[i]
                i += 1

        # Tronque proprement si besoin
        if len(texte_nettoye) > MAX_CHAR:
            # Trouve le dernier espace avant MAX_CHAR
            last_space = texte_nettoye.rfind(" ", 0, MAX_CHAR)
            if last_space > 0:
                return texte_nettoye[:last_space] + "..."
            else:
                return texte_nettoye[:MAX_CHAR] + "..."

        # Ajoute des points si besoin
        if texte_nettoye.endswith("."):
            return texte_nettoye + ".."
        return texte_nettoye + "..."

    def clean_contenu(self):
        """Nettoie le contenu HTML"""
        contenu = self.contenu

        # Supprime tous les <br> et <br/>
        contenu = re.sub(r"<br\s*/?>", "", contenu)

        # <p ...> + espaces/retours à la ligne + </p>
        contenu = re.sub(r"<p[^>]*>\s*</p>", "", contenu)

        # Supprime les espaces multiples entre les balises
        contenu = re.sub(r">\s+<", "><", contenu)

        return contenu

    def save(self, *args, **kwargs):

        # on crée la date_derniere_publication
        if self.pk:
            old_instance = Article.objects.get(pk=self.pk)
            if old_instance.est_publie != self.est_publie:
                self.date_derniere_publication = timezone.now().date()
        else:
            if self.est_publie:
                self.date_derniere_publication = timezone.now().date()

        # Nettoie le contenu avant sauvegarde
        self.contenu = self.clean_contenu()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre

    class Meta:
        ordering = ["-date_derniere_publication"]
        permissions = [
            ("peut_ecrire_actu", "Peut écrire des actualités"),
            ("peut_ecrire_rpresse", "Peut écrire des revues de presse"),
            ("peut_ecrire_rh", "Peut écrire des articles RH"),
            ("peut_ecrire_adm", "Peut écrire des articles d'administration générale"),
            ("peut_ecrire_outil", "Peut écrire des articles d'outils interne"),
            ("peut_ecrire_si", "Peut écrire des articles SI"),
        ]


def custom_attachment_upload_to(instance, filename):
    # Génère un nom de fichier avec extension .jpg
    filename = f"{uuid.uuid4().hex}.jpg"
    return f"django-summernote/{timezone.now().strftime('%Y-%m-%d')}/{filename}"


class CustomAttachment(AbstractAttachment):
    """modèle utilisé par django-summernote pour le traitement des images téléchargées sur le serveur"""

    file = models.FileField(upload_to=custom_attachment_upload_to)
    est_utilisee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    # *args: nombre arbitraire d'arguments en tant que tuples
    # **kwargs: nombre arbitraire d'arguments en tant que dictionnaire

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file and hasattr(self.file, "path") and os.path.exists(self.file.path):
            self.formatage_image()

    def formatage_image(self, *args, **kwargs):
        service = ConversionAvifService()
        succes, resultat = service.convertir_fichier(
            path=self.file.path, supprimer_original=True
        )

        if succes:
            self.file.name = os.path.relpath(
                resultat, start=settings.MEDIA_ROOT
            ).replace("\\", "/")
            super().save(update_fields=["file"])
        else:
            logger.error(f"Erreur conversion AVIF: {resultat}")

    class Meta:
        verbose_name = "Image Summernote"
        verbose_name_plural = "Images Summernote"


class OutilInterne(Article):
    lien_outil = models.URLField(
        max_length=300, blank=True, null=True, validators=[validate_url]
    )

    def save(self, *args, **kwargs):
        self.categorie = "OUTIL"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Outil interne"
        verbose_name_plural = "Outils internes"
