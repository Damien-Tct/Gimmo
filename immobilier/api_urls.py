from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

router = DefaultRouter()
router.register(r'proprietaires', views_api.ProprietaireViewSet)
router.register(r'biens', views_api.BienImmobilierViewSet)
router.register(r'locataires', views_api.LocataireViewSet)
router.register(r'garants', views_api.GarantViewSet)
router.register(r'baux', views_api.BailViewSet)
router.register(r'paiements', views_api.PaiementViewSet)
router.register(r'documents', views_api.DocumentViewSet)
router.register(r'interventions', views_api.InterventionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('dashboard/', views_api.DashboardStatsAPIView.as_view(), name='api_dashboard'),
]
