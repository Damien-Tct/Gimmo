from django.urls import path
from . import views
from . import views_portail

app_name = 'immobilier'

urlpatterns = [
    # Redirection racine selon le profil
    path('', views_portail.RedirectDashboardView.as_view(), name='dashboard_redirect'),
    
    # Dashboard admin
    path('admin-dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Biens
    path('biens/', views.BienListView.as_view(), name='bien_list'),
    path('biens/ajouter/', views.BienCreateView.as_view(), name='bien_create'),
    path('biens/<int:pk>/', views.BienDetailView.as_view(), name='bien_detail'),
    path('biens/<int:pk>/modifier/', views.BienUpdateView.as_view(), name='bien_update'),
    path('biens/<int:pk>/supprimer/', views.BienDeleteView.as_view(), name='bien_delete'),
    path('biens/<int:pk>/photos/ajouter/', views.PhotoBienCreateView.as_view(), name='photo_bien_create'),
    
    # Propriétaires
    path('proprietaires/', views.ProprietaireListView.as_view(), name='proprietaire_list'),
    path('proprietaires/ajouter/', views.ProprietaireCreateView.as_view(), name='proprietaire_create'),
    path('proprietaires/<int:pk>/', views.ProprietaireDetailView.as_view(), name='proprietaire_detail'),
    path('proprietaires/<int:pk>/modifier/', views.ProprietaireUpdateView.as_view(), name='proprietaire_update'),
    path('proprietaires/<int:pk>/supprimer/', views.ProprietaireDeleteView.as_view(), name='proprietaire_delete'),
    
    # Locataires
    path('locataires/', views.LocataireListView.as_view(), name='locataire_list'),
    path('locataires/ajouter/', views.LocataireCreateView.as_view(), name='locataire_create'),
    path('locataires/<int:pk>/', views.LocataireDetailView.as_view(), name='locataire_detail'),
    path('locataires/<int:pk>/modifier/', views.LocataireUpdateView.as_view(), name='locataire_update'),
    path('locataires/<int:pk>/supprimer/', views.LocataireDeleteView.as_view(), name='locataire_delete'),
    
    # Garants
    path('locataires/<int:pk>/garants/ajouter/', views.GarantCreateView.as_view(), name='garant_create'),
    
    # Baux
    path('baux/', views.BailListView.as_view(), name='bail_list'),
    path('baux/ajouter/', views.BailCreateView.as_view(), name='bail_create'),
    path('baux/<int:pk>/', views.BailDetailView.as_view(), name='bail_detail'),
    path('baux/<int:pk>/modifier/', views.BailUpdateView.as_view(), name='bail_update'),
    path('baux/<int:pk>/supprimer/', views.BailDeleteView.as_view(), name='bail_delete'),
    
    # Paiements
    path('paiements/', views.PaiementListView.as_view(), name='paiement_list'),
    path('paiements/<int:pk>/supprimer/', views.PaiementDeleteView.as_view(), name='paiement_delete'),
    path('baux/<int:pk>/paiements/ajouter/', views.PaiementCreateView.as_view(), name='paiement_create'),
    path('paiements/<int:pk>/quittance/', views.generate_quittance, name='paiement_quittance'),
    path('baux/<int:pk>/appel-loyer/', views.generate_appel_loyer, name='bail_appel_loyer'),
    path('baux/<int:pk>/consentement-rgpd/', views.generate_consentement_rgpd, name='bail_consentement_rgpd'),
    
    # Appels de loyer groupés
    path('appels-loyers/', views.AppelsLoyersView.as_view(), name='appels_loyers'),
    path('appels-loyers/generer/', views.generer_appels_loyers_masse, name='appels_loyers_generer'),
    path('appels-loyers/<int:pk>/supprimer/', views.supprimer_appel_loyer, name='appels_loyers_supprimer'),
    
    # Documents
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/ajouter/', views.DocumentCreateView.as_view(), name='document_create'),
    path('documents/<int:pk>/supprimer/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Interventions
    path('interventions/', views.InterventionListView.as_view(), name='intervention_list'),
    path('interventions/ajouter/', views.InterventionCreateView.as_view(), name='intervention_create'),
    path('interventions/<int:pk>/', views.InterventionDetailView.as_view(), name='intervention_detail'),
    path('interventions/<int:pk>/modifier/', views.InterventionUpdateView.as_view(), name='intervention_update'),
    path('interventions/<int:pk>/supprimer/', views.InterventionDeleteView.as_view(), name='intervention_delete'),
    
    # ===================================================================
    # PORTAL LOCATAIRE
    # ===================================================================
    path('portail/', views_portail.PortailAccueilView.as_view(), name='portail_accueil'),
    path('portail/bail/', views_portail.PortailBailView.as_view(), name='portail_bail'),
    path('portail/paiements/', views_portail.PortailPaiementsView.as_view(), name='portail_paiements'),
    path('portail/interventions/', views_portail.PortailInterventionsView.as_view(), name='portail_interventions'),
    path('portail/interventions/ajouter/', views_portail.PortailInterventionCreateView.as_view(), name='portail_intervention_create'),
    path('portail/documents/', views_portail.PortailDocumentsView.as_view(), name='portail_documents'),
    path('portail/documents/ajouter/', views_portail.PortailDocumentUploadView.as_view(), name='portail_document_upload'),
    # Portail: mot de passe
    path('portail/mot-de-passe/', views_portail.PortailPasswordChangeView.as_view(), name='portail_password_change'),
    
    # Gestion des utilisateurs
    path('comptes/gerer/<int:locataire_id>/', views_portail.gerer_compte_locataire, name='gerer_compte_locataire'),
    path('comptes/creer_gestionnaire/', views_portail.creer_utilisateur_gestionnaire, name='creer_utilisateur_gestionnaire'),
    
    # RGPD & Consentement
    path('portail/consentement-rgpd/', views_portail.PortailConsentementRGPDView.as_view(), name='portail_consentement_rgpd'),

    # RGPD & Mentions légales
    path('rgpd/', views.RgpdView.as_view(), name='rgpd'),
]

