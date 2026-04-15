from django.test import TestCase
from django.urls import reverse
from .models import Article
import datetime

"""
class NewsletterViewsTests(TestCase):

    def setUp(self):
        date_test = datetime.date(2025, 10, 1)
        Article.objects.create(
            titre="Article 1", date_derniere_publication=date_test, contenu="Contenu 1"
        )
        Article.objects.create(
            titre="Article 2", date_derniere_publication=date_test, contenu="Contenu 2"
        )

    def test_index_view_status_code(self):
        response = self.client.get(reverse("newsletter:index"))
        self.assertEqual(response.status_code, 200)

    def test_index_view_template_used(self):
        response = self.client.get(reverse("newsletter:index"))
        self.assertTemplateUsed(response, "newsletter/index.html")

    def test_index_view_lists_articles(self):
        response = self.client.get(reverse("newsletter:index"))
        self.assertContains(response, "Article 1")
        self.assertContains(response, "Article 2")

    def test_detail_view_status_code(self):
        date_test = datetime.date(2025, 10, 1)
        article = Article.objects.create(
            titre="Article détail",
            date_derniere_publication=date_test,
            contenu="Contenu de test de l'article",
        )
        response = self.client.get(reverse("newsletter:detail", args=[article.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Article détail")
        self.assertEqual(article.date_derniere_publication, date_test)
        self.assertContains(response, "Contenu de test de l'article")
"""
