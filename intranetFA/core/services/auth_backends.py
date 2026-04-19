# core/services/auth_backends.py
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from ldap3 import Server, Connection, ALL, SIMPLE
from ldap3.utils.conv import escape_filter_chars
import logging

logger = logging.getLogger("core")


class LDAP3Backend(BaseBackend):
    """
    Authentification Active Directory via ldap3.
    Les utilisateurs sont créés sans droits, l'admin Django leur attribue ensuite les permissions.
    """

    def authenticate(self, request, **credentials):
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return None

        if "@" not in username:
            email = f"{username}@{settings.LDAP_EMAIL_DOMAIN}"
        else:
            email = username

        try:
            server = Server(settings.LDAP_SERVER_URI, get_info=ALL)

            # Connexion avec compte de services
            conn_search = Connection(
                server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True,
            )
            try:
                # Recherche de l'utilisateur
                conn_search.search(
                    search_base=settings.LDAP_BASE_DN,
                    search_filter=f"(mail={escape_filter_chars(email)})",
                    attributes=["givenName", "sn", "mail"],
                )

                if not conn_search.entries:
                    logger.warning(f"Utilisateur {email} non trouvé dans l'AD")
                    return None

                # On est sensé n'avoir qu'une seule entrée, problème du coté de l'AD sinon
                entry = conn_search.entries[0]
                user_dn = entry.entry_dn
                first_name = entry.givenName.value if "givenName" in entry else ""
                last_name = entry.sn.value if "sn" in entry else ""
                mail = entry.mail.value if "mail" in entry else email
            finally:
                conn_search.unbind()

            # Validation du mot de passe
            try:
                conn_user = Connection(
                    server,
                    user=user_dn,
                    password=password,
                    authentication=SIMPLE,
                    auto_bind=True,
                )
                conn_user.unbind()
                logger.info(f"Authentification AD réussie pour {email}")
            except Exception as e:
                logger.warning(f"Echec de connexion pour {email}")
                return None

            # Création/Mise à jour de l'utilisateur Django
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    "email": mail,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )

            # Mise à jour des infos personnelles
            if not created:
                user.first_name = first_name
                user.last_name = last_name
                user.email = mail
                user.save()

            # On indique a Django quel backend à été utilisé pour authentifier l'utilisateur
            user.backend = f"{self.__module__}.{self.__class__.__name__}"
            action = "créé" if created else "connecté"
            logger.info(f"Utilisateur {action}: {email} (staff={user.is_staff})")

            return user

        except Exception as e:
            logger.error(f"Erreur LDAP pour {email}: {type(e).__name__}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
