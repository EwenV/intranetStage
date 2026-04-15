from django.shortcuts import render
from .services import get_ldap_entries
import json
from django.core.cache import cache
import logging

logger = logging.getLogger("trombinoscope")


def trombinoscope_view(request):
    ldap_entries = get_ldap_entries()

    search_term = request.GET.get("search", "").strip().lower()

    # Filtrer si un terme de recherche est présent
    if search_term:
        ldap_entries = [
            entry
            for entry in ldap_entries
            if (
                search_term in entry.get("name", "").lower()
                or search_term in entry.get("givenName", "").lower()
                or search_term in entry.get("mail", "").lower()
                or search_term in entry.get("department", "").lower()
                or search_term in entry.get("title", "").lower()
                or search_term.replace(" ", "")
                in entry.get("telephoneNumber", "").replace(" ", "")
                or search_term.replace(" ", "")
                in entry.get("mobile", "").replace(" ", "")
            )
        ]

    context = {"ldap_entries": ldap_entries}
    if request.headers.get("HX-Request"):
        return render(request, "trombinoscope/_trombinoscope_grid.html", context)
    return render(request, "trombinoscope/trombinoscope.html", context)
