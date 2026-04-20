# newsletter/signals.py
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Article, CustomAttachment
import os


logger = logging.getLogger("newsletter")
NB_IMG_SUPPRIMEE_MAX = 100


# Déclenché après la sauvegarde d'un article
@receiver(post_save, sender=Article)
def manage_article_images(sender, instance, **kwargs):
    # 1. Marquer les images de cet article comme utilisées
    if instance.contenu:
        used_images = instance.get_images_utilisees()
        used_images.update(est_utilisee=True)

    # 2. Nettoyage léger des vieilles images orphelines
    date_max = timezone.now() - timedelta(hours=48)  # 48h de délai

    img_non_utilisee = CustomAttachment.objects.filter(
        est_utilisee=False, date_creation__lt=date_max
    )[:NB_IMG_SUPPRIMEE_MAX]

    for img in img_non_utilisee:
        try:
            if os.path.exists(img.file.path):
                os.remove(img.file.path)
            img.delete()
        except Exception as e:
            logger.error(
                f"Erreur lors du nettoyage de l'image orpheline {img.pk} "
                f"(fichier: {img.file.name}): {e}"
            )


# Déclenché avant la suppression d'un article
@receiver(pre_delete, sender=Article)
def cleanup_article_images(sender, instance, **kwargs):
    used_images = instance.get_images_utilisees()

    for attachment in used_images:
        try:
            if os.path.exists(attachment.file.path):
                os.remove(attachment.file.path)
            attachment.delete()
        except Exception as e:
            logger.error(
                f"Erreur lors de la suppression de l'image {attachment.pk} "
                f"(fichier: {attachment.file.name}) de l'article '{instance.titre}': {e}"
            )
