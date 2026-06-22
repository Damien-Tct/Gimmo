import django_filters
from django.db.models import Q
from .models import (
    Proprietaire, BienImmobilier, Locataire,
    Bail, Paiement, Intervention
)


class ProprietaireFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Recherche')
    ville = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Proprietaire
        fields = ['q', 'ville', 'actif']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(nom__icontains=value) |
            Q(prenom__icontains=value) |
            Q(raison_sociale__icontains=value) |
            Q(email__icontains=value) |
            Q(ville__icontains=value)
        )


class BienImmobilierFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Recherche')
    prix_max = django_filters.NumberFilter(field_name='loyer_mensuel_indicatif', lookup_expr='lte')

    class Meta:
        model = BienImmobilier
        fields = {
            'type_bien': ['exact'],
            'statut': ['exact'],
            'ville': ['icontains'],
            'nombre_pieces': ['gte', 'lte'],
            'surface_habitable': ['gte', 'lte'],
            'meuble': ['exact'],
            'proprietaire': ['exact'],
            'actif': ['exact'],
        }

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(titre__icontains=value) |
            Q(ville__icontains=value) |
            Q(adresse__icontains=value) |
            Q(description__icontains=value)
        )


class LocataireFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Recherche')
    ville = django_filters.CharFilter(lookup_expr='icontains')
    actif = django_filters.BooleanFilter(method='filter_actif', label='Actif')

    class Meta:
        model = Locataire
        fields = ['q', 'ville', 'actif']

    def filter_actif(self, queryset, name, value):
        from datetime import date
        today = date.today()
        if value:
            return queryset.filter(baux__actif=True, baux__date_fin__gte=today).distinct()
        return queryset.exclude(baux__actif=True, baux__date_fin__gte=today).distinct()

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(nom__icontains=value) |
            Q(prenom__icontains=value) |
            Q(email__icontains=value) |
            Q(ville__icontains=value)
        )


class BailFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Recherche')
    date_debut = django_filters.DateFromToRangeFilter()
    date_fin = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Bail
        fields = {
            'type_bail': ['exact'],
            'actif': ['exact'],
            'resiliation': ['exact'],
            'bien': ['exact'],
            'locataire': ['exact'],
            'loyer_mensuel': ['gte', 'lte'],
        }

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(numero_contrat__icontains=value) |
            Q(bien__titre__icontains=value) |
            Q(locataire__nom__icontains=value) |
            Q(locataire__prenom__icontains=value)
        )


class PaiementFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Recherche')
    date_paiement = django_filters.DateFromToRangeFilter()
    date_periode_debut = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Paiement
        fields = {
            'statut': ['exact'],
            'mode_paiement': ['exact'],
            'montant': ['gte', 'lte'],
        }

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(bail__numero_contrat__icontains=value) |
            Q(locataire__nom__icontains=value) |
            Q(reference__icontains=value)
        )


class InterventionFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Recherche')
    date_soumission = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Intervention
        fields = {
            'statut': ['exact'],
            'priorite': ['exact'],
            'bien': ['exact'],
        }

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(titre__icontains=value) |
            Q(description__icontains=value) |
            Q(bien__titre__icontains=value) |
            Q(prestataire_nom__icontains=value)
        )
