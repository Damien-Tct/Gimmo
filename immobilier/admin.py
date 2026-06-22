from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Proprietaire, BienImmobilier, PhotoBien, Locataire, Garant,
    Bail, Paiement, Document, Intervention
)


# ===================================================================
# Inlines
# ===================================================================
class PhotoBienInline(admin.TabularInline):
    model = PhotoBien
    extra = 1
    fields = ['image', 'legende', 'est_principale']


class BailInline(admin.TabularInline):
    model = Bail
    extra = 0
    fields = ['numero_contrat', 'locataire', 'date_debut', 'date_fin', 'loyer_mensuel', 'actif']
    readonly_fields = ['numero_contrat']
    show_change_link = True


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
    fields = ['date_paiement', 'montant', 'statut', 'mode_paiement']
    readonly_fields = ['date_creation']
    show_change_link = True


class InterventionInline(admin.TabularInline):
    model = Intervention
    extra = 0
    fields = ['titre', 'statut', 'priorite', 'date_soumission']
    readonly_fields = ['date_soumission']
    show_change_link = True


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ['titre', 'categorie', 'fichier']
    show_change_link = True


# ===================================================================
# Admin: Propriétaire
# ===================================================================
@admin.register(Proprietaire)
class ProprietaireAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'type_personne', 'email', 'telephone', 'ville', 'get_nb_biens', 'actif', 'date_creation']
    list_filter = ['type_personne', 'actif', 'ville', 'pays']
    search_fields = ['nom', 'prenom', 'raison_sociale', 'email', 'ville']
    fieldsets = (
        ("Type", {'fields': ('type_personne',)}),
        ("Identité", {'fields': ('civilite', 'nom', 'prenom', 'raison_sociale', 'siret')}),
        ("Contact", {'fields': ('email', 'telephone', 'telephone_secondaire')}),
        ("Adresse", {'fields': ('adresse', 'code_postal', 'ville', 'pays')}),
        ("Bancaire", {'fields': ('iban', 'bic')}),
        ("Informations", {'fields': ('notes', 'actif')}),
    )


# ===================================================================
# Admin: Bien Immobilier
# ===================================================================
@admin.register(BienImmobilier)
class BienImmobilierAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_bien', 'statut', 'ville', 'surface_habitable', 'nombre_pieces', 'loyer_mensuel_indicatif', 'proprietaire', 'actif']
    list_filter = ['type_bien', 'statut', 'meuble', 'ascenseur', 'ville', 'actif']
    search_fields = ['titre', 'adresse', 'ville', 'description']
    inlines = [PhotoBienInline, BailInline, InterventionInline, DocumentInline]
    fieldsets = (
        ("Général", {'fields': ('proprietaire', 'type_bien', 'statut', 'titre', 'description')}),
        ("Adresse", {'fields': ('adresse', 'complement_adresse', 'code_postal', 'ville', 'quartier', 'pays')}),
        ("Caractéristiques", {'fields': (
            'surface_totale', 'surface_habitable', 'nombre_pieces', 'nombre_chambres',
            'etage', 'nombre_etages_total', 'annee_construction',
            'mode_chauffage', 'classe_energie', 'classe_ges'
        )}),
        ("Équipements", {'fields': (
            'meuble', 'ascenseur', 'balcon', 'parking', 'cave', 'jardin',
            'piscine', 'interphone', 'gardien', 'acces_handicap'
        )}),
        ("Financier", {'fields': ('loyer_mensuel_indicatif', 'charges_indicatives', 'depot_garantie_mois', 'taxe_fonciere')}),
        ("Media", {'fields': ('photo_principale',)}),
        ("Informations", {'fields': ('notes', 'actif')}),
    )


# ===================================================================
# Admin: Locataire
# ===================================================================
@admin.register(Locataire)
class LocataireAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email', 'telephone', 'ville', 'get_bien_actuel', 'statut_actif', 'date_creation']
    list_filter = ['ville']
    search_fields = ['nom', 'prenom', 'email', 'ville']
    fieldsets = (
        ("Identité", {'fields': ('civilite', 'nom', 'prenom', 'date_naissance')}),
        ("Contact", {'fields': ('email', 'telephone', 'telephone_secondaire')}),
        ("Adresse", {'fields': ('adresse', 'code_postal', 'ville', 'pays')}),
        ("Professionnel", {'fields': ('profession', 'employeur')}),
        ("Documents", {'fields': ('piece_identite', 'justificatif_domicile', 'justificatif_revenus')}),
        ("Bancaire", {'fields': ('iban',)}),
        ("Informations", {'fields': ('notes',)}),
    )

    def statut_actif(self, obj):
        return obj.est_actif
    statut_actif.boolean = True
    statut_actif.short_description = 'Actif'


# ===================================================================
# Admin: Garant
# ===================================================================
@admin.register(Garant)
class GarantAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'locataire', 'email', 'telephone', 'revenus_mensuels']
    list_filter = ['locataire']
    search_fields = ['nom', 'prenom', 'locataire__nom']


# ===================================================================
# Admin: Bail
# ===================================================================
@admin.register(Bail)
class BailAdmin(admin.ModelAdmin):
    list_display = ['numero_contrat', 'bien', 'locataire', 'date_debut', 'date_fin', 'loyer_mensuel', 'actif', 'resiliation', 'est_en_cours']
    list_filter = ['type_bail', 'actif', 'resiliation', 'modalite_paiement']
    search_fields = ['numero_contrat', 'bien__titre', 'locataire__nom', 'locataire__prenom']
    inlines = [PaiementInline, DocumentInline]
    fieldsets = (
        ("Identification", {'fields': ('numero_contrat', 'type_bail')}),
        ("Parties", {'fields': ('bien', 'locataire', 'colocataires')}),
        ("Dates", {'fields': ('date_debut', 'date_fin', 'duree_mois', 'tacite_reconduction', 'preavis_mois')}),
        ("Financier", {'fields': (
            'loyer_mensuel', 'charges_mensuelles', 'provision_charges',
            'depot_garantie', 'depot_garantie_encaisse', 'depot_garantie_restitué',
            'modalite_paiement', 'jour_paiement'
        )}),
        ("Révision", {'fields': ('indice_revision', 'date_prochaine_revision', 'montant_annuel_revision')}),
        ("État des lieux", {'fields': (
            'date_etat_lieux_entree', 'etat_lieux_entree',
            'date_etat_lieux_sortie', 'etat_lieux_sortie'
        )}),
        ("Assurances & Clauses", {'fields': (
            'assurance_locataire', 'assurance_proprietaire',
            'clause_resolutoire', 'solidarite_colocataires'
        )}),
        ("Statut", {'fields': ('actif', 'resiliation', 'date_resiliation', 'motif_resiliation', 'notes')}),
    )

    def est_en_cours(self, obj):
        return obj.est_en_cours()
    est_en_cours.boolean = True
    est_en_cours.short_description = 'En cours'


# ===================================================================
# Admin: Paiement
# ===================================================================
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['id', 'bail', 'locataire', 'montant', 'date_paiement', 'statut', 'mode_paiement', 'quittance_generee']
    list_filter = ['statut', 'mode_paiement', 'date_paiement']
    search_fields = ['bail__numero_contrat', 'locataire__nom', 'reference']
    date_hierarchy = 'date_paiement'
    fieldsets = (
        ("Informations", {'fields': ('bail', 'locataire', 'montant', 'montant_charges')}),
        ("Période", {'fields': ('date_paiement', 'date_periode_debut', 'date_periode_fin')}),
        ("Détails", {'fields': ('mode_paiement', 'reference', 'statut')}),
        ("Quittance", {'fields': ('quittance_generee', 'quittance_pdf')}),
        ("Notes", {'fields': ('notes',)}),
    )


# ===================================================================
# Admin: Document
# ===================================================================
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'bien', 'locataire', 'proprietaire', 'date_creation']
    list_filter = ['categorie']
    search_fields = ['titre', 'notes']


# ===================================================================
# Admin: Intervention
# ===================================================================
@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ['titre', 'bien', 'statut', 'priorite', 'date_soumission', 'date_planification', 'cout_estime']
    list_filter = ['statut', 'priorite']
    search_fields = ['titre', 'description', 'bien__titre']
    fieldsets = (
        ("Description", {'fields': ('bien', 'locataire', 'titre', 'description')}),
        ("Suivi", {'fields': ('statut', 'priorite', 'date_soumission', 'date_debut', 'date_fin', 'date_planification')}),
        ("Prestataire", {'fields': ('prestataire_nom', 'prestataire_telephone', 'prestataire_email')}),
        ("Coûts", {'fields': ('cout_estime', 'cout_reel', 'devis', 'facture')}),
        ("Notes", {'fields': ('notes',)}),
    )


# ===================================================================
# Photo - Admin simple
# ===================================================================
@admin.register(PhotoBien)
class PhotoBienAdmin(admin.ModelAdmin):
    list_display = ['bien', 'legende', 'est_principale', 'date_upload']
    list_filter = ['est_principale']
