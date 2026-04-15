⚠️ Documentation WIP ⚠️

# Intranet FA

Intranet d'entreprise pour Fougères Agglomération développé avec Django.

## Fonctionnalités

- **Newsletter** : Gestion d'articles avec éditeur riche (Summernote)
- **Trombinoscope** : Annuaire des employés via LDAP Active Directory
- **Fiches réflexes** : Bibliothèque documentaire avec aperçus PDF
- **Organigramme** : Gestion et affichage de l'organigramme
- **Rapports d'activité** : Archive des rapports annuels

## Technologies

- Django 5.2.6
- PostgreSQL
- LDAP (Active Directory)
- Django Summernote
- Conversion automatique AVIF

## Installation

1. Cloner le repository
2. Installer les dépendances avec Poetry :
   ```bash
   poetry install
   ```
3. Copier `.env.exemple` vers `.env` et configurer les variables
4. Appliquer les migrations :
   ```bash
   python intranetFA/manage.py migrate
   ```
5. Créer un superutilisateur :
   ```bash
   python intranetFA/manage.py createsuperuser
   ```
6. Lancer le serveur :
   ```bash
   python intranetFA/manage.py runserver
   ```

## Configuration

Le projet utilise des variables d'environnement pour la configuration. Voir `.env.exemple` pour les variables requises.

## Auteur

Ewen Vuichard - Stage SI Fougères Agglomération
