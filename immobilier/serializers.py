from rest_framework import serializers
from .models import (
    Proprietaire, BienImmobilier, PhotoBien, Locataire, Garant,
    Bail, Paiement, Document, Intervention
)


# ---------------------------------------------------------------------------
# Propriétaire
# ---------------------------------------------------------------------------
class ProprietaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proprietaire
        fields = '__all__'


class ProprietaireListSerializer(serializers.ModelSerializer):
    nb_biens = serializers.IntegerField(source='get_nb_biens', read_only=True)

    class Meta:
        model = Proprietaire
        fields = ['id', 'nom', 'prenom', 'raison_sociale', 'email',
                  'telephone', 'ville', 'actif', 'nb_biens', 'date_creation']


# ---------------------------------------------------------------------------
# Bien Immobilier
# ---------------------------------------------------------------------------
class PhotoBienSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoBien
        fields = ['id', 'image', 'legende', 'est_principale', 'date_upload']


class BienImmobilierListSerializer(serializers.ModelSerializer):
    proprietaire_nom = serializers.SerializerMethodField()
    locataire_actuel = serializers.SerializerMethodField()
    loyer_actuel = serializers.SerializerMethodField()

    class Meta:
        model = BienImmobilier
        fields = ['id', 'type_bien', 'titre', 'statut', 'ville',
                  'surface_habitable', 'nombre_pieces', 'loyer_mensuel_indicatif',
                  'proprietaire_nom', 'locataire_actuel', 'loyer_actuel',
                  'photo_principale', 'actif', 'date_creation']

    def get_proprietaire_nom(self, obj):
        return str(obj.proprietaire)

    def get_locataire_actuel(self, obj):
        loc = obj.get_locataire_actuel()
        return str(loc) if loc else None

    def get_loyer_actuel(self, obj):
        return float(obj.get_loyer_actuel()) if obj.get_loyer_actuel() else None


class BienImmobilierSerializer(serializers.ModelSerializer):
    photos = PhotoBienSerializer(many=True, read_only=True)
    proprietaire_nom = serializers.SerializerMethodField()

    class Meta:
        model = BienImmobilier
        fields = '__all__'

    def get_proprietaire_nom(self, obj):
        return str(obj.proprietaire)


# ---------------------------------------------------------------------------
# Locataire
# ---------------------------------------------------------------------------
class GarantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garant
        fields = '__all__'


class LocataireListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locataire
        fields = ['id', 'nom', 'prenom', 'email', 'telephone',
                  'ville', 'actif', 'date_creation']


class LocataireSerializer(serializers.ModelSerializer):
    garants = GarantSerializer(many=True, read_only=True)
    bien_actuel = serializers.SerializerMethodField()

    class Meta:
        model = Locataire
        fields = '__all__'

    def get_bien_actuel(self, obj):
        bien = obj.get_bien_actuel()
        return str(bien) if bien else None


# ---------------------------------------------------------------------------
# Bail
# ---------------------------------------------------------------------------
class BailListSerializer(serializers.ModelSerializer):
    bien_titre = serializers.CharField(source='bien.titre', read_only=True)
    locataire_nom = serializers.SerializerMethodField()

    class Meta:
        model = Bail
        fields = ['id', 'numero_contrat', 'bien_titre', 'locataire_nom',
                  'date_debut', 'date_fin', 'loyer_mensuel',
                  'actif', 'resiliation']

    def get_locataire_nom(self, obj):
        return str(obj.locataire)


class BailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bail
        fields = '__all__'


# ---------------------------------------------------------------------------
# Paiement
# ---------------------------------------------------------------------------
class PaiementListSerializer(serializers.ModelSerializer):
    locataire_nom = serializers.SerializerMethodField()
    bail_numero = serializers.CharField(source='bail.numero_contrat', read_only=True)

    class Meta:
        model = Paiement
        fields = ['id', 'bail_numero', 'locataire_nom', 'montant',
                  'mode_paiement', 'date_paiement', 'statut']

    def get_locataire_nom(self, obj):
        return str(obj.locataire) if obj.locataire else '—'


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'categorie', 'titre', 'fichier', 'date_creation']


# ---------------------------------------------------------------------------
# Intervention
# ---------------------------------------------------------------------------
class InterventionListSerializer(serializers.ModelSerializer):
    bien_titre = serializers.CharField(source='bien.titre', read_only=True)

    class Meta:
        model = Intervention
        fields = ['id', 'titre', 'bien_titre', 'statut', 'priorite',
                  'date_soumission', 'cout_estime', 'cout_reel']


class InterventionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intervention
        fields = '__all__'
