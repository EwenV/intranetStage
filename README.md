# Intranet Stage Fougères Agglomération

Intranet développé en **Python / Django** lors de mon stage de deux mois au service informatique de Fougères Agglomération. L'application centralise les outils de communication interne et l'annuaire des agents, par manque de temps elle n'a cependant pas été déployée sur les serveurs de l'agglomération.

## Fonctionnalités

| Module | Description |
|---|---|
| **Newsletter** | Gestion et publication d'articles avec éditeur WYSIWYG (Summernote) |
| **Trombinoscope** | Annuaire des agents synchronisé avec l'Active Directory via LDAP(S), avec photo, poste et coordonnées |
| **Fiches réflexes** | Bibliothèque de fiches d'informations PDF |
| **Outils internes** | Catalogue de liens vers des outils métiers, avec descriptions et mode d'emploi sous forme d'un article |
| **Organigramme** | Affichage de l'organigramme (PDF converti en image pour affichage) |
| **Rapports d'activité** | Liste des rapports annuels en PDF |

### Points notables

- **Conversion des images en AVIF** : un service dédié (`ConversionAvifService`) convertit toutes les images uploadées (articles, fiches, organigramme) en format AVIF avec redimensionnement et nettoyage des métadonnées EXIF, réduisant significativement le poids des images et pdf stockés.
- **Recherche dynamique** via HTMX (requêtes partielles sans rechargement de page) et Alpine.js.
- **Système de permissions Django** : chaque catégorie d'article possède sa permission Django, permettant plus de contrôle à l'administrateur.
- **Cache LDAP** cache simple pour les informations du trombinoscope, afin de limiter les requêtes vers l'Active Directory.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | Python 3.12+, Django 5.2 |
| Base de données | PostgreSQL |
| Connection Active Directory | ldap3 |
| Éditeur d'articles | django-summernote |
| Frontend | HTML/CSS, Alpine.js, HTMX |
| Traitement d'images | Pillow, pillow-avif-plugin, pdf2image |
| Gestion des dépendances | Poetry |
| Variables d'environnement | python-dotenv |
| Linting | djlint |

---

## Sécurité

### Ce que Django gère nativement

Django fournit de base un ensemble de protections activées automatiquement :

| Protection | Mécanisme Django | Description |
|---|---|---|
| **CSRF** | `CsrfViewMiddleware` | Un token unique est injecté dans chaque formulaire POST, protégeant les attaques CSRF |
| **XSS (auto-échappement)** | Moteur de templates | Toutes les variables `{{ var }}` sont automatiquement échappées en HTML. Les caractères `<`, `>`, `&`, `"`, `'` sont convertis en texte (ex: '<' = '&lt'). Attention tous de même au contexte (ex : <script>var x = {{ var }}</script>)|
| **Injection SQL** | ORM QuerySet | Les requêtes via l'ORM sont paramétrisées : le code SQL d’une requête est défini séparément de ses paramètres. |
| **Clickjacking** | `XFrameOptionsMiddleware` | Envoie un header `X-Frame-Options: DENY` pour empêcher l'intégration de la page dans une iframe malveillante |
| **Gestion des sessions** | `SessionMiddleware` | Sessions côté serveur avec identifiants aléatoires, rotation des IDs, expiration configurable |
| **Hachage des mots de passe** | module `auth` | Configuration par défaut : PBKDF2 avec sel, les mots de passe ne sont jamais stockés en clair |
| **Validation des mots de passe** | `AUTH_PASSWORD_VALIDATORS` | 4 validateurs actifs : similarité avec les attributs utilisateur, longueur minimale, mots de passe courants, mots de passe uniquement numériques |
| **Host header validation** | `ALLOWED_HOSTS` | Seuls les domaines listés sont acceptés, prévenant les attaques par manipulation du header Host |

### Ce que j'ai implémenté

Au-delà des protections natives de Django, j'ai mis en place les mesures suivantes :

#### Authentification LDAP sécurisée
- **Backend d'authentification custom** (`LDAP3Backend`) qui authentifie les utilisateurs contre l'Active Directory via le protocole LDAP
- **Protection contre l'injection LDAP** : utilisation de `escape_filter_chars()` de la librairie `ldap3` pour échapper les caractères spéciaux (`*`, `(`, `)`, `\`, `\0`) dans les filtres de recherche LDAP

#### Sanitisation HTML
Le champ contenu des articles utilise un éditeur riche (Summernote) qui produit du HTML brut. Deux couches de protection :
1. **En entrée** (écriture en base) : `SummernoteTextField` nettoye le HTML et supprime les balises/attributs dangereux (`<script>`, `onerror`, etc.)
2. **En sortie** (affichage dans les vues) : sanitisation supplémentaire avec la librairie `nh3` avant le rendu

#### Validation des URLs
- Les champs URL des outils internes sont validés pour n'accepter que les schémas `http://` et `https://`, bloquant les vecteurs d'attaque de type `javascript:` ou `data:`

#### Configuration sécurisée
- Clé secrète, mots de passe PostgreSQL/LDAP et autres données importantes stockées dans un .env non commit (voir .env.exemple)
- **Limite de taille des uploads** pour prévenir les abus

#### Nettoyage des métadonnées EXIF
- Le service de conversion AVIF supprime la plupart des métadonnées EXIF, ne conservant que les métadonnées utiles

### Prérequis avant déploiement en production
- [ ] Passer de LDAP à **LDAPS** pour chiffrer 
      les échanges avec l'Active Directory
- [ ] Configurer HTTPS et activer les headers de sécurité associés
      (`SECURE_SSL_REDIRECT`, `HSTS`, `SESSION_COOKIE_SECURE`)
- [ ] Protection brute-force sur le login (`django-axes`) notamment contre les DDoS (attaque par déni de service) 
- [ ] Audit des dépendances (`pip-audit` ou Dependabot)

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
   
3. **Activer l'environnement poetry:**
   ```bash
   poetry shell
   ```

4. **Configurer l'environnement :**
   ```bash
   cp .env.exemple .env
   ```
   Puis renseigner les variables dans `.env` (voir les commentaires dans `.env.exemple`).

   Pour générer une clé secrète Django :
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **Appliquer les migrations :**
   ```bash
   python intranetFA/manage.py migrate
   ```

6. **Créer un superutilisateur :**
   ```bash
   python intranetFA/manage.py createsuperuser
   ```

7. **Lancer le serveur de développement :**
   ```bash
   python intranetFA/manage.py runserver
   ```

L'application est alors accessible sur `http://localhost:8000`.

---

## Auteur

**Ewen Vuichard** - Stage au Service Informatique de Fougères Agglomération
