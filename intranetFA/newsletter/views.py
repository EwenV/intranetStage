from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from newsletter.models import Article
from newsletter.models import OutilInterne
import json
from django.core.paginator import Paginator
from django.db.models import Q, Value
from django.db.models.functions import Concat


def index_view(request):
    articles = Article.objects.filter(est_publie=True)

    search_term = request.GET.get("search", "").strip()
    categorie = request.GET.get("categorie", "")
    sort_order = request.GET.get("sort_order", "desc")

    # Filtrer par catégorie
    if categorie:
        articles = articles.filter(categorie=categorie)

    # Filtrer par recherche
    if search_term:
        articles = articles.annotate(
            auteur_full_name=Concat(
                "auteur__first_name", Value(" "), "auteur__last_name"
            ),
            auteur_full_name_revert=Concat(
                "auteur__last_name", Value(" "), "auteur__first_name"
            ),
        ).filter(
            Q(titre__icontains=search_term)
            | Q(contenu__icontains=search_term)
            | Q(categorie__icontains=search_term)
            | Q(auteur_full_name__icontains=search_term)
            | Q(auteur_full_name_revert__icontains=search_term)
            | Q(auteur__email__icontains=search_term)
            | Q(date_derniere_publication__icontains=search_term)
        )

    # Tri par date
    if sort_order == "asc":
        articles = articles.order_by("date_derniere_publication")
    else:
        articles = articles.order_by("-date_derniere_publication")

    # Pagination
    paginator = Paginator(articles, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "articles": page_obj.object_list,
        "categories": Article.CATEGORIES,
    }
    # Si requête htmx, renvoyer seulement le fragment
    if request.headers.get("HX-Request"):
        return render(request, "newsletter/_articles_list.html", context)
    return render(request, "newsletter/index.html", context)


def detail_view(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if article.est_publie:
        return render(request, "newsletter/article.html", {"article": article})

    user = request.user
    if user.is_authenticated and (user == article.auteur or user.is_superuser):
        return render(request, "newsletter/article.html", {"article": article})

    return redirect("newsletter:index")


def index_outil_view(request):
    outils_internes = OutilInterne.objects.filter(est_publie=True).order_by("titre")
    return render(
        request, "newsletter/index_outil.html", {"outils_internes": outils_internes}
    )


def detail_outil_view(request, pk):
    outil_interne = get_object_or_404(OutilInterne, pk=pk)

    if outil_interne.est_publie:
        return render(request, "newsletter/article.html", {"article": outil_interne})

    user = request.user
    if user.is_authenticated and (user == outil_interne.auteur or user.is_superuser):
        return render(request, "newsletter/article.html", {"article": outil_interne})

    return render(request, "newsletter/index_outil.html", {"article": outil_interne})
