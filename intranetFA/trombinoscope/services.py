from ldap3 import Connection
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
import base64
import binascii
import logging

logger = logging.getLogger("trombinoscope")

ATTRIBUTES = [
    "name",
    "givenName",
    "telephoneNumber",
    "mobile",
    "mail",
    "department",
    "title",
    "thumbnailPhoto",
]
CACHE_TIMEOUT = 24 * 60 * 60  # 24 heures


def find_fa_employees():
    # Convertit les valeurs LDAP en chaînes propres
    def clean(value):
        if isinstance(value, list):
            return " ".join(str(v) for v in value)
        if value is None:
            return ""
        return str(value)

    conn = Connection(
        settings.LDAP_SERVER_URI,
        user=settings.LDAP_BIND_DN,
        password=settings.LDAP_BIND_PASSWORD,
        auto_bind=True,
    )
    conn.search(
        settings.LDAP_BASE_DN,
        "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))",
        attributes=ATTRIBUTES,
    )

    ldap_entries = []
    for entry in conn.entries:
        thumbnail = ""
        # Conversion bytes -> base64 si la photo existe
        if "thumbnailPhoto" in entry and entry["thumbnailPhoto"].value is not None:
            try:
                hex_data = entry["thumbnailPhoto"].value
                logger.debug(
                    f"Données brutes (type={type(hex_data)}): {hex_data[:20]}..."
                )
                binary_data = hex_data
                thumbnail = base64.b64encode(binary_data).decode("utf-8")

            except (TypeError, binascii.Error) as e:
                logger.error(
                    f"Erreur de conversion pour {entry.get('name', 'inconnu')}: {e}"
                )
                thumbnail = ""

        entry_data = {
            "dn": clean(entry.entry_dn),
            "name": clean(entry["name"].value if "name" in entry else ""),
            "givenName": clean(
                entry["givenName"].value if "givenName" in entry else ""
            ),
            "telephoneNumber": clean(
                entry["telephoneNumber"].value if "telephoneNumber" in entry else ""
            ),
            "mobile": clean(entry["mobile"].value if "mobile" in entry else ""),
            "mail": clean(entry["mail"].value if "mail" in entry else ""),
            "department": clean(
                entry["department"].value if "department" in entry else ""
            ),
            "title": clean(entry["title"].value if "title" in entry else ""),
            "thumbnailPhoto": thumbnail,
        }
        if entry_data["mobile"] or entry_data["telephoneNumber"] and entry_data["mail"]:
            ldap_entries.append(entry_data)

    conn.unbind()
    return ldap_entries


def get_ldap_entries():
    ldap_entries = cache.get("ldap_entries")
    if ldap_entries is None:
        ldap_entries = find_fa_employees()
        cache.set("ldap_entries", ldap_entries, timeout=CACHE_TIMEOUT)
    return ldap_entries
