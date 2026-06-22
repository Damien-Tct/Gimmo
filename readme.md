# 🏠 Application de Gestion Immobilière

Application web complète de gestion de biens immobiliers développée avec **Django 5.1**.

## 📋 Fonctionnalités

### 1. Gestion des Biens Immobiliers
- Création, modification, consultation et suppression de biens (appartements, maisons, locaux commerciaux, terrains)
- Caractéristiques détaillées (surface, étage, nombre de pièces, DPE, etc.)
- Upload de photos et documents associés
- Statut (disponible, loué, en travaux, vendu)

### 2. Gestion des Propriétaires
- Fiche complète avec coordonnées
- Historique des biens possédés
- Documents associés

### 3. Gestion des Locataires
- Fiche complète avec coordonnées
- Dossier de candidature (documents uploadés)
- Historique des locations
- Garants

### 4. Gestion des Baux
- Création et suivi des contrats de location
- Dates d'entrée et de sortie
- Montant du loyer et charges
- Dépôt de garantie
- État des lieux
- Révisions de loyer automatiques

### 5. Gestion des Paiements
- Encaissement des loyers
- Quittances de loyer générées automatiquement
- Suivi des impayés
- Historique complet
- Modes de paiement (virement, chèque, espèces)

### 6. Gestion des Documents
- Upload et stockage de tous types de documents
- Catégorisation (bail, état des lieux, DPE, diagnostic, facture, etc.)
- Association aux biens, locataires ou propriétaires
- Documents par contrat

### 7. Gestion des Interventions
- Demandes d'intervention des locataires
- Suivi des travaux et réparations
- Devis et factures associés
- Statut (à faire, en cours, terminé)
- Priorité (basse, moyenne, haute, urgente)

### 8. Dashboard & Statistiques
- Vue d'ensemble du parc immobilier
- Indicateurs clés (taux d'occupation, loyers perçus, impayés)
- Graphiques d'évolution
- Alertes (baux expirant, interventions urgentes, impayés)

### 9. Recherche & Filtres Avancés
- Recherche multi-critères
- Filtres par statut, type, ville, montant, dates

### 10. API REST
- API complète avec Django REST Framework
- Authentification token
- Endpoints pour chaque entité

## 🏗️ Arborescence du Projet

```
Appli_gemini/
├── manage.py
├── readme.md
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── immobilier/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── serializers.py
│   ├── filters.py
│   ├── decorators.py
│   ├── utils.py
│   ├── context_processors.py
│   ├── validators.py
│   ├── permissions.py
│   ├── templates/
│   │   └── immobilier/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── bien_list.html
│   │       ├── bien_detail.html
│   │       ├── bien_form.html
│   │       ├── proprietaire_list.html
│   │       ├── proprietaire_detail.html
│   │       ├── proprietaire_form.html
│   │       ├── locataire_list.html
│   │       ├── locataire_detail.html
│   │       ├── locataire_form.html
│   │       ├── bail_list.html
│   │       ├── bail_detail.html
│   │       ├── bail_form.html
│   │       ├── paiement_list.html
│   │       ├── paiement_form.html
│   │       ├── quittance.html
│   │       ├── document_list.html
│   │       ├── document_form.html
│   │       ├── intervention_list.html
│   │       ├── intervention_detail.html
│   │       └── intervention_form.html
│   └── static/
│       └── immobilier/
│           ├── css/
│           │   └── style.css
│           ├── js/
│           │   └── main.js
│           └── img/
└── media/
    ├── photos/
    ├── documents/
    └── uploads/
```

## 🚀 Installation

1. **Cloner le projet**
```bash
git clone <votre-repo>
cd Appli_gemini
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install django django-crispy-forms crispy-bootstrap5 django-filter djangorestframework pillow reportlab matplotlib
```

4. **Appliquer les migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

6. **Lancer le serveur**
```bash
python manage.py runserver
```

7. **Accéder à l'application**
- Interface web : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/
- API : http://127.0.0.1:8000/api/

## 🔧 Technologies Utilisées

- **Django 6** - Framework web
- **Django REST Framework** - API REST
- **Crispy Forms + Bootstrap 5** - Formulaires stylisés
- **django-filter** - Recherche et filtres avancés
- **Pillow** - Traitement d'images
- **ReportLab** - Génération de PDF (quittances)
- **Matplotlib** - Graphiques pour le dashboard
- **SQLite** - Base de données (développement)
