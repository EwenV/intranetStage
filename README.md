# Intranet Fougères Agglomération

Intranet développé en **Python / Django** lors de mon stage au service SI de Fougères Agglomération. L'application centralise les outils de communication interne et l'annuaire des agents, hébergée sur les serveurs de l'agglomération et accessible uniquement depuis le réseau interne.

---

## Fonctionnalités

| Module | Description |
|---|---|
| **Newsletter** | Gestion et publication d'articles avec éditeur WYSIWYG riche (Summernote), filtrage par catégorie, recherche en temps réel et pagination |
| **Trombinoscope** | Annuaire des agents synchronisé avec l'Active Directory via LDAP, avec photo, poste et coordonnées |
| **Fiches réflexes** | Bibliothèque de fiches documentaires PDF avec aperçu image auto-généré |
| **Outils internes** | Catalogue de liens vers les outils métiers, avec descriptions éditables |
| **Organigramme** | Affichage de l'organigramme (PDF converti en image pour un affichage web rapide) |
| **Rapports d'activité** | Archive des rapports annuels en PDF |

### Points techniques notables

- **Conversion automatique des images en AVIF** : un service dédié (`ConversionAvifService`) convertit toutes les images uploadées (articles, fiches, organigramme) en format AVIF avec redimensionnement et nettoyage des métadonnées EXIF, réduisant significativement le poids des assets.
- **Recherche dynamique** via HTMX (requêtes partielles sans rechargement de page) et Alpine.js pour la réactivité côté client.
- **Système de permissions granulaire** : chaque catégorie d'article possède sa propre permission Django, permettant à l'administrateur de contrôler finement qui peut publier quoi.
- **Nettoyage automatique des images orphelines** via des signals Django (`post_save`, `pre_delete`) pour éviter l'accumulation de fichiers inutilisés sur le serveur.
- **Cache LDAP** avec invalidation automatique (24h) pour limiter les requêtes vers l'Active Directory.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | Python 3.12+, Django 5.2 |
| Base de données | PostgreSQL |
| Annuaire | LDAP / Active Directory (via `ldap3`) |
| Éditeur d'articles | Django Summernote |
| Frontend | HTML/CSS, Alpine.js, HTMX |
| Traitement d'images | Pillow, pillow-avif-plugin, pdf2image |
| Gestion des dépendances | Poetry |
| Linting templates | djlint |

---

## Architecture du projet

```
intranetFA/
├── core/                   # App transversale : organigramme, rapports, services partagés
│   ├── services/
│   │   ├── auth_backends.py      # Backend d'authentification LDAP custom
│   │   └── conversion_avif.py    # Service de conversion images/PDF → AVIF
│   ├── models.py                 # Organigramme, RapportActivite
│   └── views.py
├── newsletter/             # App principale : articles, outils internes
│   ├── models.py                 # Article, OutilInterne, CustomAttachment
│   ├── signals.py                # Nettoyage automatique des images orphelines
│   ├── admin.py                  # Interface d'administration personnalisée
│   └── views.py
├── trombinoscope/          # Annuaire LDAP
│   ├── services.py               # Requêtes LDAP, mise en cache
│   └── views.py
├── fiche_reflexes/         # Fiches documentaires PDF
│   ├── models.py                 # FicheReflexes (PDF + aperçu AVIF)
│   └── views.py
├── templates/              # Templates globaux (base.html, header)
├── static/                 # CSS, JS (Alpine, HTMX), images, polices
└── intranetFA/             # Configuration Django (settings, urls)
```

---

## Sécurité

### Ce que Django gère nativement

Django fournit de base un ensemble de protections activées automatiquement :

| Protection | Mécanisme Django | Description |
|---|---|---|
| **CSRF** | `CsrfViewMiddleware` | Un token unique est injecté dans chaque formulaire POST, empêchant les requêtes forgées depuis un site tiers |
| **XSS (auto-échappement)** | Moteur de templates | Toutes les variables `{{ var }}` sont automatiquement échappées en HTML. Les caractères `<`, `>`, `&`, `"`, `'` sont convertis en entités HTML |
| **Injection SQL** | ORM QuerySet | Les requêtes via l'ORM sont paramétrisées : les valeurs utilisateur ne sont jamais concaténées dans le SQL |
| **Clickjacking** | `XFrameOptionsMiddleware` | Envoie un header `X-Frame-Options: DENY` pour empêcher l'intégration de la page dans une iframe malveillante |
| **Gestion des sessions** | `SessionMiddleware` | Sessions côté serveur avec identifiants aléatoires, rotation des IDs, expiration configurable |
| **Hachage des mots de passe** | `auth` module | PBKDF2 avec sel par défaut, les mots de passe ne sont jamais stockés en clair |
| **Validation des mots de passe** | `AUTH_PASSWORD_VALIDATORS` | 4 validateurs actifs : similarité avec les attributs utilisateur, longueur minimale, mots de passe courants, mots de passe uniquement numériques |
| **Host header validation** | `ALLOWED_HOSTS` | Seuls les domaines listés sont acceptés, prévenant les attaques par manipulation du header Host |

### Ce que j'ai implémenté moi-même

Au-delà des protections natives de Django, j'ai mis en place les mesures suivantes :

#### Authentification LDAP sécurisée
- **Backend d'authentification custom** (`LDAP3Backend`) qui authentifie les utilisateurs contre l'Active Directory via le protocole LDAP
- **Principe du moindre privilège** : les utilisateurs créés via LDAP ont `is_staff=False` et `is_superuser=False` par défaut. L'administrateur attribue ensuite manuellement les permissions nécessaires
- **Protection contre l'injection LDAP** : utilisation de `escape_filter_chars()` de la librairie `ldap3` pour échapper les caractères spéciaux (`*`, `(`, `)`, `\`, `\0`) dans les filtres de recherche LDAP
- **Connexion via un compte de service** dédié (bind DN) plutôt qu'un accès anonyme à l'annuaire

#### Sanitisation HTML (défense en profondeur)
Le champ contenu des articles utilise un éditeur riche (Summernote) qui produit du HTML brut. Deux couches de protection :
1. **En entrée** (écriture en base) : `SummernoteTextField` utilise `bleach` pour nettoyer le HTML et supprimer les balises/attributs dangereux (`<script>`, `onerror`, etc.)
2. **En sortie** (affichage dans les vues) : sanitisation supplémentaire avec la librairie `nh3` avant le rendu, en plus du filtre `|safe` dans les templates

#### Contrôle d'accès aux articles non publiés
- Les articles non publiés ne sont visibles que par leur auteur ou un superutilisateur, permettant la prévisualisation avant publication sans exposer le contenu aux autres utilisateurs
- L'interface d'administration Django est personnalisée pour que chaque éditeur ne voie que ses propres articles

#### Validation des URLs
- Les champs URL des outils internes sont validés pour n'accepter que les schémas `http://` et `https://`, bloquant les vecteurs d'attaque de type `javascript:` ou `data:`

#### Configuration sécurisée
- **`SECRET_KEY` externalisée** dans les variables d'environnement via `.env`, jamais commitée dans le code source
- **`DEBUG` désactivé par défaut** (`False`), activable uniquement par variable d'environnement
- **Logging structuré** avec rotation des fichiers de log (`RotatingFileHandler`), niveaux configurables par module
- **Limite de taille des uploads** (`DATA_UPLOAD_MAX_MEMORY_SIZE = 6 Mo`) pour prévenir les abus

#### Nettoyage des métadonnées EXIF
- Le service de conversion AVIF supprime les métadonnées EXIF sensibles des images uploadées (données GPS, informations de l'appareil, etc.), ne conservant que les métadonnées strictement utiles

#### Minimisation des données LDAP
- L'annuaire ne récupère que les attributs nécessaires à l'affichage (nom, prénom, téléphone, email, service, poste, photo), sans exposer les DN complets ni les informations techniques de l'Active Directory

### Améliorations prévues

- [ ] Protection brute-force sur le login (ex: `django-axes`)
- [ ] Headers de sécurité HTTPS (`SECURE_SSL_REDIRECT`, `HSTS`, `SESSION_COOKIE_SECURE`) — à activer au déploiement
- [ ] Audit régulier des dépendances avec `pip-audit` ou Dependabot

---

## Installation

### Prérequis

- Python 3.12+
- PostgreSQL
- [Poetry](https://python-poetry.org/) (gestionnaire de dépendances)
- poppler-utils (pour la conversion PDF → image : `sudo apt install poppler-utils`)
- Un accès à un Active Directory (pour le trombinoscope et l'authentification LDAP)

### Étapes

1. **Cloner le repository :**
   ```bash
   git clone https://github.com/EwenV/intranetStage.git
   cd intranetStage
   ```

2. **Installer les dépendances :**
   ```bash
   poetry install
   ```

3. **Configurer l'environnement :**
   ```bash
   cp .env.exemple .env
   ```
   Puis renseigner les variables dans `.env` (voir les commentaires dans `.env.exemple`).

   Pour générer une clé secrète Django :
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Appliquer les migrations :**
   ```bash
   python intranetFA/manage.py migrate
   ```

5. **Créer un superutilisateur :**
   ```bash
   python intranetFA/manage.py createsuperuser
   ```

6. **Lancer le serveur de développement :**
   ```bash
   python intranetFA/manage.py runserver
   ```

L'application est alors accessible sur `http://localhost:8000`. L'interface d'administration est sur `/admin/`.

---

## Auteur

**Ewen Vuichard** — Stage SI, Fougères Agglomération
