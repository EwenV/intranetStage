import os
from PIL import Image, ExifTags
from pdf2image import convert_from_path
import logging
from typing import Tuple, Dict


logger = logging.getLogger("core")


class ConversionAvifService:
    """Service de conversion d'image et PDF en avif"""

    METADONNEES_UTILES = {"DateTimeOriginal", "GPSInfo"}

    def convertir_fichier(
        self,
        path: str,
        supprimer_original: bool,
        num_page: int | None = None,
        image_qualite: int = 50,
        img_largeur_max: int = 1600,
        img_hauteur_max: int = 1600,
        pdf_dpi: int = 200,
    ) -> Tuple[bool, str]:
        """Convertit un fichier image ou PDF en AVIF"""

        if not os.path.exists(path):
            return False, f"Fichier introuvable: {path}"

        f_extension = os.path.splitext(path)[1].lower()

        try:
            if f_extension == ".pdf":
                if not num_page:
                    logger.warning(f"num_page non spécifié pour le PDF: {path}")
                    return False, f"num_page non spécifié pour le PDF: {path}"
                return self._convertir_pdf_en_avif(
                    path,
                    supprimer_original,
                    num_page,
                    image_qualite,
                    img_largeur_max,
                    img_hauteur_max,
                    pdf_dpi,
                )
            else:
                return self._convertir_image_en_avif(
                    path,
                    supprimer_original,
                    image_qualite,
                    img_largeur_max,
                    img_hauteur_max,
                )
        except Exception as e:
            logger.exception(f"Erreur inattendue lors de la conversion de {path}")
            return False, f"Erreur inattendue: {str(e)}"

    def _convertir_image_en_avif(
        self,
        path: str,
        supprimer_original: bool,
        image_qualite: int = 50,
        img_largeur_max: int = 1600,
        img_hauteur_max: int = 1600,
    ) -> Tuple[bool, str]:
        try:
            with Image.open(path) as img:
                # Conversion en RGB si nécessaire
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                img = self._redimensionner_image(img, img_largeur_max, img_hauteur_max)
                new_exif = self._nettoyer_metadonnees(img)
                # Nouveau chemin qui correspond à notre nouvelle extension
                new_path = os.path.splitext(path)[0] + ".avif"

                # Sauvegarde en AVIF, en utilisant new_exif,
                img.save(new_path, "AVIF", quality=image_qualite, exif=new_exif)

                if supprimer_original and path != new_path:
                    self._supprimer_fichier_original(path)

                logger.info(f"Image convertie: {new_path}")
                return True, new_path
        except Exception as e:
            logger.error(f"Erreur conversion d'image: {path}")
            return False, f"Erreur conversion d'image : {str(e)}"

    def _convertir_pdf_en_avif(
        self,
        path: str,
        supprimer_original: bool,
        num_page: int,
        image_qualite: int = 50,
        img_largeur_max: int = 1600,
        img_hauteur_max: int = 1600,
        pdf_dpi: int = 200,
    ) -> Tuple[bool, str]:
        """Conversion d'une page d'un fichier PDF en image AVIF
        ! Les métadonnées du PDF ne sont pas transférées à la nouvelle image
        """

        try:
            img = convert_from_path(
                path, dpi=pdf_dpi, first_page=num_page, last_page=num_page
            )[0]
        except Exception as e:
            logger.error(f"Erreur lecture PDF {path}: {e}")
            return False, f"Erreur lecture PDF: {str(e)}"

        if not img:
            msg = f"La page {num_page} n'existe pas"
            logger.warning(f"{msg}: {path}")
            return False, msg

        try:
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
        except Exception as e:
            logger.error(f"Erreur conversion RGB {path}: {e}")
            return False, f"Erreur conversion RGB: {str(e)}"

        img = self._redimensionner_image(img, img_largeur_max, img_hauteur_max)
        # Nouveau chemin qui correspond à notre nouvelle extension
        new_path = os.path.splitext(path)[0] + ".avif"

        # Sauvegarde en AVIF
        try:
            img.save(new_path, "AVIF", quality=image_qualite)
        except Exception as e:
            logger.error(f"Erreur sauvegarde AVIF {new_path}: {e}")
            return False, f"Erreur sauvegarde AVIF {str(e)}"

        if supprimer_original and path != new_path:
            self._supprimer_fichier_original(path)

        logger.info(f"PDF converti: {new_path}")
        return True, new_path

    def _supprimer_fichier_original(self, path: str) -> None:
        try:
            os.remove(path)
            logger.info(f"Fichier original supprimé: {path}")
        except Exception as e:
            logger.warning(f"Impossible de supprimer le fichier original: {e}")

    def _redimensionner_image(
        self, img: Image.Image, img_largeur_max: int, img_hauteur_max: int
    ) -> Image.Image:
        max_size = (img_largeur_max, img_hauteur_max)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            # LANCZOS est un filtre de rééchantillonnage
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img

    def _nettoyer_metadonnees(self, img: Image.Image) -> Dict:
        exif = img.getexif()
        new_exif = {}
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag in self.METADONNEES_UTILES:
                new_exif[tag_id] = value
        return new_exif
