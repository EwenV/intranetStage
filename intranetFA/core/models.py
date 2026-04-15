from django.db import models
import logging
import os
from core.services.conversion_avif import ConversionAvifService
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


logger = logging.getLogger("core")


class Organigramme(models.Model):
    fichier_pdf = models.FileField(upload_to="organigramme/", max_length=255)
    fichier_avif = models.FileField(
        upload_to="organigramme/", blank=True, null=True, editable=False, max_length=255
    )
    date_mise_a_jour = models.DateField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        # Empêche plus d'une instance
        if not self.pk and Organigramme.objects.exists():
            raise ValidationError(
                "Une instance d'Organigramme existe déjà. Veuillez la modifier au lieu d'en créer une nouvelle."
            )

        if not os.path.splitext(self.fichier_pdf.name)[1].lower() == ".pdf":
            logger.error(f"Fichier {self.fichier_pdf} non PDF")
            raise ValidationError("Le fichier doit être un PDF (.pdf).")

        super().save(*args, **kwargs)

        try:
            service = ConversionAvifService()
            succes, resultat = service.convertir_fichier(
                path=self.fichier_pdf.path,
                supprimer_original=False,
                num_page=1,
                image_qualite=60,
                img_largeur_max=6400,
                img_hauteur_max=6400,
                pdf_dpi=300,
            )
            if not succes:
                logger.error(f"Echec conversion: {self.fichier_pdf}: {resultat}")
                return

            # Met à jour le champ fichier_avif avec le chemin de l'AVIF généré
            self.fichier_avif.name = os.path.relpath(
                resultat, start=settings.MEDIA_ROOT
            ).replace("\\", "/")
            logger.info(
                f"Avif généré pour {self.fichier_pdf}: {self.fichier_avif.name}"
            )

        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la conversion AVIF pour {self.fichier_pdf}: {e}"
            )
            raise ValueError(f"Erreur de conversion: {e}")

        super().save(update_fields=["fichier_avif"])

    def __str__(self):
        return os.path.basename(self.fichier_pdf.name)

    class Meta:
        verbose_name = "Organigramme"
        verbose_name_plural = "Organigramme"


class RapportActivite(models.Model):
    fichier_pdf = models.FileField(upload_to="rapports_activite/", max_length=255)
    date = models.DateField()

    def save(self, *args, **kwargs):

        if not os.path.splitext(self.fichier_pdf.name)[1].lower() == ".pdf":
            logger.error(f"Fichier {self.fichier_pdf} non PDF")
            raise ValidationError("Le fichier doit être un PDF (.pdf).")

        super().save(*args, **kwargs)

    def __str__(self):
        return os.path.basename(self.fichier_pdf.name)

    class Meta:
        verbose_name = "Rapport d'Activité"
        verbose_name_plural = "Rapports d'Activité"
