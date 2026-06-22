from .models import Intervention, Bail, Paiement
from datetime import date, timedelta
from django.utils import timezone


def site_processor(request):
    """Context processor fournissant des données globales au menu/templates."""
    alerts = []
    
    # Baux expirant dans les 90 jours
    baux_expirant = Bail.objects.filter(
        actif=True, resiliation=False,
        date_fin__gte=date.today(),
        date_fin__lte=date.today() + timedelta(days=90)
    ).count()
    if baux_expirant > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-calendar-exclamation',
            'message': f'{baux_expirant} bail(x) expire(nt) dans les 90 jours',
            'count': baux_expirant
        })
    
    # Interventions urgentes
    urgentes = Intervention.objects.filter(
        priorite='URG', statut__in=['AFAI', 'ENCO']
    ).count()
    if urgentes > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-exclamation-triangle',
            'message': f'{urgentes} intervention(s) urgente(s)',
            'count': urgentes
        })
    
    # Impayés
    impayes = Paiement.objects.filter(statut='EN_RETARD').count()
    if impayes > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-currency-euro',
            'message': f'{impayes} paiement(s) en retard',
            'count': impayes
        })
    
    return {
        'global_alerts': alerts,
        'site_name': 'Gestion Immobilière',
        'year': timezone.now().year,
    }
