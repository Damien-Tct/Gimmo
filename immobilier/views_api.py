"""
API REST - Views
"""
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Proprietaire, BienImmobilier, Locataire, Garant,
    Bail, Paiement, Document, Intervention,
    StatutIntervention
)
from .serializers import (
    ProprietaireSerializer, ProprietaireListSerializer,
    BienImmobilierSerializer, BienImmobilierListSerializer,
    LocataireSerializer, LocataireListSerializer,
    GarantSerializer,
    BailSerializer, BailListSerializer,
    PaiementSerializer, PaiementListSerializer,
    DocumentSerializer, DocumentListSerializer,
    InterventionSerializer, InterventionListSerializer
)
from .permissions import IsAdminOrReadOnly


class ProprietaireViewSet(viewsets.ModelViewSet):
    queryset = Proprietaire.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProprietaireListSerializer
        return ProprietaireSerializer


class BienImmobilierViewSet(viewsets.ModelViewSet):
    queryset = BienImmobilier.objects.select_related('proprietaire').all()
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['titre', 'ville', 'adresse', 'description']
    filterset_fields = ['type_bien', 'statut', 'ville', 'meuble', 'actif']

    def get_serializer_class(self):
        if self.action == 'list':
            return BienImmobilierListSerializer
        return BienImmobilierSerializer

    @action(detail=True, methods=['get'])
    def baux(self, request, pk=None):
        bien = self.get_object()
        baux = Bail.objects.filter(bien=bien)
        serializer = BailListSerializer(baux, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def paiements(self, request, pk=None):
        bien = self.get_object()
        paiements = Paiement.objects.filter(bail__bien=bien)
        serializer = PaiementListSerializer(paiements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def interventions(self, request, pk=None):
        bien = self.get_object()
        interventions = Intervention.objects.filter(bien=bien)
        serializer = InterventionListSerializer(interventions, many=True)
        return Response(serializer.data)


class LocataireViewSet(viewsets.ModelViewSet):
    queryset = Locataire.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nom', 'prenom', 'email', 'ville']

    def get_serializer_class(self):
        if self.action == 'list':
            return LocataireListSerializer
        return LocataireSerializer

    @action(detail=True, methods=['get'])
    def baux(self, request, pk=None):
        locataire = self.get_object()
        baux = Bail.objects.filter(locataire=locataire)
        serializer = BailListSerializer(baux, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def paiements(self, request, pk=None):
        locataire = self.get_object()
        paiements = Paiement.objects.filter(locataire=locataire)
        serializer = PaiementListSerializer(paiements, many=True)
        return Response(serializer.data)


class GarantViewSet(viewsets.ModelViewSet):
    queryset = Garant.objects.all()
    serializer_class = GarantSerializer
    permission_classes = [permissions.IsAuthenticated]


class BailViewSet(viewsets.ModelViewSet):
    queryset = Bail.objects.select_related('bien', 'locataire').all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['actif', 'type_bail', 'resiliation']
    search_fields = ['numero_contrat']

    def get_serializer_class(self):
        if self.action == 'list':
            return BailListSerializer
        return BailSerializer

    @action(detail=True, methods=['get'])
    def paiements(self, request, pk=None):
        bail = self.get_object()
        paiements = Paiement.objects.filter(bail=bail)
        serializer = PaiementListSerializer(paiements, many=True)
        return Response(serializer.data)


class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.select_related('bail', 'locataire').all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['statut', 'mode_paiement']

    def get_serializer_class(self):
        if self.action == 'list':
            return PaiementListSerializer
        return PaiementSerializer

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        paiement = self.get_object()
        paiement.statut = 'VALID'
        paiement.save()
        return Response({'status': 'Paiement validé'})

    @action(detail=True, methods=['post'])
    def marquer_impaye(self, request, pk=None):
        paiement = self.get_object()
        paiement.statut = 'EN_RETARD'
        paiement.save()
        return Response({'status': 'Paiement marqué comme impayé'})


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['categorie']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        return DocumentSerializer


class InterventionViewSet(viewsets.ModelViewSet):
    queryset = Intervention.objects.select_related('bien').all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['statut', 'priorite']

    def get_serializer_class(self):
        if self.action == 'list':
            return InterventionListSerializer
        return InterventionSerializer

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        intervention = self.get_object()
        nouveau_statut = request.data.get('statut')
        if nouveau_statut in dict(Intervention.StatutIntervention.choices):
            intervention.statut = nouveau_statut
            intervention.save()
            return Response({'status': f'Statut changé en {intervention.get_statut_display()}'})
        return Response({'error': 'Statut invalide'}, status=400)


class DashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .utils import get_dashboard_stats
        stats = get_dashboard_stats()
        return Response(stats)
