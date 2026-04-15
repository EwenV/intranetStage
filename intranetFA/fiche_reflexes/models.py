from django.db import models
from core.services.conversion_avif import ConversionAvifService
import logging
import os
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

logger = logging.getLogger("fiche_reflexes")


class FicheReflexes(models.Model):
    titre = models.CharField(max_length=100)
    fichier_pdf = models.FileField(upload_to="fiche_reflexes/", max_length=255)
    fichier_avif = models.FileField(
        upload_to="fiche_reflexes/",
        blank=True,
        null=True,
        editable=False,
        max_length=255,
    )
    date_ajout = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if not os.path.splitext(self.fichier_pdf.name)[1].lower() == ".pdf":
            logger.error(f"Fichier {self.titre} non PDF")
            raise ValidationError("Le fichier doit être un PDF (.pdf).")

        super().save(*args, **kwargs)

        try:
            service = ConversionAvifService()
            succes, resultat = service.convertir_fichier(
                path=self.fichier_pdf.path, supprimer_original=False, num_page=1
            )
            if not succes:
                logger.error(f"Echec conversion: {self.titre}: {resultat}")
                return

            # Met à jour le champ fichier_avif avec le chemin de l'AVIF généré
            self.fichier_avif.name = os.path.relpath(
                resultat, start=settings.MEDIA_ROOT
            ).replace("\\", "/")
            logger.info(f"Avif généré pour {self.titre}: {self.fichier_avif.name}")

        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la conversion AVIF pour {self.titre}: {e}"
            )
            raise ValueError(f"Erreur de conversion: {e}")

        super().save(update_fields=["fichier_avif"])

    def __str__(self):
        return self.titre

    class Meta:
        verbose_name = "Fiche réflexes"
        verbose_name_plural = "Fiches réflexes"
