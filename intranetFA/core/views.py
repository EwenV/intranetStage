from django.shortcuts import render
from core.models import Organigramme, RapportActivite
from django.http import Http404


def organigramme_view(request):
    organigramme = Organigramme.objects.first()

    return render(request, "core/organigramme.html", {"organigramme": organigramme})


def rapport_activite_view(request):
    rapports = RapportActivite.objects.all().order_by("-date")
    return render(request, "core/rapports-activite.html", {"rapports": rapports})
