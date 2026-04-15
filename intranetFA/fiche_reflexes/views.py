from django.shortcuts import render
from fiche_reflexes.models import FicheReflexes
import random
from django.shortcuts import redirect, get_object_or_404


def fiche_reflexes_index_view(request):
    fiches = FicheReflexes.objects.all().order_by("titre")
    return render(request, "fiche_reflexes/fiche_index.html", {"fiches": fiches})


def fiche_reflexes_view(request, pk):
    fiche = get_object_or_404(FicheReflexes, pk=pk)
    return render(request, "fiche_reflexes/fiche.html", {"fiche": fiche})


def fiche_aleatoire_redirect(request):
    pks = list(FicheReflexes.objects.values_list("pk", flat=True))
    if not pks:
        return redirect("newsletter:index")
    pk = random.choice(pks)
    return redirect("fiche_reflexes:fiche_reflexes", pk=pk)
