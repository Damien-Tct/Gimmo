"""
Vues du portail locataire et pages d'authentification personnalisée.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView, FormView, RedirectView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
import django.forms as forms

from .models import (
    Proprietaire, BienImmobilier, Locataire, Garant,
    Bail, Paiement, Document, Intervention
)
from .forms import InterventionForm


# ===================================================================
# MIXINS
# ===================================================================
class LocataireRequiredMixin(UserPassesTestMixin):
    """Vérifie que l'utilisateur connecté est un locataire."""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        # Un locataire a un profil locataire lié OU est dans le groupe 'locataire'
        return (hasattr(self.request.user, 'locataire_profile') and 
                self.request.user.locataire_profile is not None) or \
               self.request.user.groups.filter(name='Locataire').exists()


class StaffRequiredMixin(UserPassesTestMixin):
    """Vérifie que l'utilisateur est staff/gestionnaire."""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            self.request.user.groups.filter(name='Gestionnaire').exists()
        )


# ===================================================================
# AUTHENTIFICATION PERSONNALISÉE
# ===================================================================
class CustomLoginView(LoginView):
    """Page de connexion personnalisée."""
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """Forcer le changement de mot de passe si c'est le mot de passe par défaut."""
        user = form.get_user()
        login(self.request, user)
        
        # Si le mot de passe est celui par défaut et que c'est un locataire
        if user.check_password('locataire123') and user.groups.filter(name='Locataire').exists():
            messages.warning(self.request, 'Vous utilisez un mot de passe temporaire. Veuillez le changer.')
            return HttpResponseRedirect(reverse('immobilier:portail_password_change'))
        
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Gestionnaire').exists():
            return reverse_lazy('immobilier:dashboard')
        elif user.groups.filter(name='Locataire').exists():
            return reverse_lazy('immobilier:portail_accueil')
        return reverse_lazy('immobilier:dashboard')


class CustomLogoutView(LogoutView):
    """Déconnexion."""
    next_page = reverse_lazy('login')


class RedirectDashboardView(LoginRequiredMixin, RedirectView):
    """Redirige vers le bon tableau de bord selon le profil."""
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Gestionnaire').exists():
            return reverse('immobilier:dashboard')
        # Locataire ou autre → portail
        return reverse('immobilier:portail_accueil')


# ===================================================================
# ESPACE LOCATAIRE (Portail)
# ===================================================================
class PortailAccueilView(LoginRequiredMixin, TemplateView):
    """Page d'accueil de l'espace locataire."""
    template_name = 'immobilier/portail/accueil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Utiliser la relation directe Locataire.user
        locataire = getattr(user, 'locataire_profile', None)
        if not locataire:
            try:
                locataire = Locataire.objects.get(email=user.email)
            except Locataire.DoesNotExist:
                locataire = None
        
        if locataire:
            context['locataire'] = locataire
            context['bail_actif'] = locataire.get_bail_actif()
            context['bien'] = locataire.get_bien_actuel()
            
            if context['bail_actif']:
                context['prochain_paiement'] = context['bail_actif'].loyer_mensuel + context['bail_actif'].charges_mensuelles
                context['reste_a_payer'] = context['bail_actif'].reste_a_payer()
                
                context['derniers_paiements'] = Paiement.objects.filter(
                    locataire=locataire
                ).select_related('bail__bien').order_by('-date_paiement')[:5]
                
                # Propriétaire du bien
                if context['bien']:
                    context['proprietaire'] = context['bien'].proprietaire
                
                # Garant du locataire
                context['garants'] = Garant.objects.filter(locataire=locataire)
                
                # Chronologie des paiements (12 derniers mois)
                twelve_months_ago = date.today() - timedelta(days=365)
                context['paiements_annuels'] = Paiement.objects.filter(
                    locataire=locataire,
                    date_paiement__gte=twelve_months_ago
                ).order_by('-date_paiement')
                
                stats = Paiement.objects.filter(locataire=locataire).aggregate(
                    total_paye=Sum('montant', filter=Q(statut='VALID')),
                    impayes=Sum('montant', filter=Q(statut='EN_RETARD')),
                    nb_valid=Count('id', filter=Q(statut='VALID')),
                    nb_impaye=Count('id', filter=Q(statut='EN_RETARD'))
                )
                context['stats_paiements'] = stats
            
            context['interventions'] = Intervention.objects.filter(
                locataire=locataire
            ).order_by('-date_soumission')[:5]
            
            context['documents'] = Document.objects.filter(
                locataire=locataire
            ).order_by('-date_creation')[:5]
            
            # Paiements en attente suite à un appel de loyer
            context['paiements_en_attente'] = Paiement.objects.filter(
                locataire=locataire,
                statut='EN_ATTENTE'
            ).select_related('bail').order_by('-date_periode_debut')
            
            # Montant total dû (en attente)
            total_du = Paiement.objects.filter(
                locataire=locataire,
                statut='EN_ATTENTE'
            ).aggregate(
                total=Sum('montant') + Sum('montant_charges')
            )
            context['total_du'] = total_du['total'] or 0
            
            # Documents du bail (état des lieux, etc.)
            context['documents_bail'] = []
            if context['bail_actif']:
                bail = context['bail_actif']
                if bail.etat_lieux_entree:
                    context['documents_bail'].append({
                        'titre': "État des lieux d'entrée",
                        'fichier': bail.etat_lieux_entree.url,
                        'date': bail.date_etat_lieux_entree or '',
                    })
                if bail.etat_lieux_sortie:
                    context['documents_bail'].append({
                        'titre': "État des lieux de sortie",
                        'fichier': bail.etat_lieux_sortie.url,
                        'date': bail.date_etat_lieux_sortie or '',
                    })
        
        return context


class PortailPaiementsView(LoginRequiredMixin, TemplateView):
    """Historique des paiements du locataire."""
    template_name = 'immobilier/portail/paiements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            # Fallback : chercher un locataire avec le même email
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        
        if locataire:
            context['locataire'] = locataire
            context['paiements'] = Paiement.objects.filter(
                locataire=locataire
            ).select_related('bail__bien').order_by('-date_paiement')
            
            stats = Paiement.objects.filter(locataire=locataire).aggregate(
                total_paye=Sum('montant', filter=Q(statut='VALID')),
                total_attente=Sum('montant', filter=Q(statut='EN_ATTENTE')),
                impayes=Sum('montant', filter=Q(statut='EN_RETARD')),
            )
            context['stats'] = stats
        
        return context


class PortailInterventionsView(LoginRequiredMixin, ListView):
    """Liste des interventions du locataire."""
    template_name = 'immobilier/portail/interventions.html'
    context_object_name = 'interventions'
    paginate_by = 10

    def get_queryset(self):
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            # Fallback : chercher un locataire avec le même email
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            return Intervention.objects.filter(
                locataire=locataire
            ).select_related('bien').order_by('-date_soumission')
        return Intervention.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            # Fallback : chercher un locataire avec le même email
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            context['locataire'] = locataire
            context['bien'] = locataire.get_bien_actuel()
        return context


class PortailInterventionCreateView(LoginRequiredMixin, CreateView):
    """Création d'une intervention par le locataire."""
    model = Intervention
    form_class = InterventionForm
    template_name = 'immobilier/portail/intervention_form.html'
    success_url = reverse_lazy('immobilier:portail_interventions')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            # Fallback : chercher un locataire avec le même email
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        
        if locataire:
            bien = locataire.get_bien_actuel()
            if bien:
                form.fields['bien'].initial = bien
                form.fields['bien'].queryset = BienImmobilier.objects.filter(pk=bien.pk)
            # Cacher les champs admin et les rendre non-obligatoires
            for field in ['bien', 'locataire', 'statut', 'prestataire_nom', 'prestataire_telephone', 
                         'prestataire_email', 'cout_estime', 'cout_reel', 'devis', 'facture', 'notes']:
                if field in form.fields:
                    form.fields[field].widget = forms.HiddenInput()
                    form.fields[field].required = False
            # Afficher le degré d'urgence avec valeur par défaut
            if 'priorite' in form.fields:
                form.fields['priorite'].initial = 'BAS'
                form.fields['priorite'].widget.attrs.update({'class': 'form-select'})
                form.fields['priorite'].label = "Degré d'urgence"
        return form

    def form_valid(self, form):
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            form.instance.locataire = locataire
            form.instance.statut = 'AFAI'
            # Forcer le bien du locataire
            bien = locataire.get_bien_actuel()
            if bien:
                form.instance.bien = bien
        messages.success(self.request, 'Votre demande d\'intervention a été envoyée.')
        return super().form_valid(form)


class PortailDocumentsView(LoginRequiredMixin, ListView):
    """Documents accessibles au locataire (quittances, baux, etc.)."""
    template_name = 'immobilier/portail/documents.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            return Document.objects.filter(locataire=locataire).order_by('-date_creation')
        return Document.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            context['locataire'] = locataire
            
            # Quittances de loyer
            context['quittances'] = Paiement.objects.filter(
                locataire=locataire,
                quittance_generee=True,
                quittance_pdf__isnull=False
            ).order_by('-date_paiement')
            
            # Appels de loyer : recherche par catégorie FACT ou par titre
            from django.db.models import Q
            context['appels_loyers'] = Document.objects.filter(
                locataire=locataire
            ).filter(
                Q(categorie='FACT') | Q(titre__icontains='appel') | Q(titre__icontains='loyer')
            ).order_by('-date_creation')
            
            # Documents du bail actif (état des lieux, DPE, contrat)
            bail_actif = locataire.get_bail_actif()
            if bail_actif:
                context['bail_actif'] = bail_actif
        return context


class PortailBailView(LoginRequiredMixin, DetailView):
    """Vue du bail actif du locataire."""
    template_name = 'immobilier/portail/bail_detail.html'
    context_object_name = 'bail'

    def get_object(self, queryset=None):
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            # Fallback : chercher un locataire avec le même email
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            return locataire.get_bail_actif()
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get('bail'):
            context['paiements'] = Paiement.objects.filter(
                bail=context['bail']
            ).order_by('-date_paiement')[:12]
        return context


class PortailDocumentUploadView(LoginRequiredMixin, CreateView):
    """Upload d'un document par le locataire."""
    model = Document
    template_name = 'immobilier/portail/document_upload.html'
    fields = ['categorie', 'titre', 'fichier', 'notes']
    success_url = reverse_lazy('immobilier:portail_documents')

    def form_valid(self, form):
        locataire = getattr(self.request.user, 'locataire_profile', None)
        if not locataire:
            # Fallback : chercher un locataire avec le même email
            try:
                locataire = Locataire.objects.get(email=self.request.user.email)
            except Locataire.DoesNotExist:
                locataire = None
        if locataire:
            form.instance.locataire = locataire
            bien = locataire.get_bien_actuel()
            if bien:
                form.instance.bien = bien
            bail = locataire.get_bail_actif()
            if bail:
                form.instance.bail = bail
        messages.success(self.request, 'Document ajouté avec succès.')
        return super().form_valid(form)


# ===================================================================
# CHANGEMENT DE MOT DE PASSE (Portail locataire)
# ===================================================================
class PortailPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Page de changement de mot de passe pour le locataire."""
    template_name = 'immobilier/portail/password_change.html'
    success_url = reverse_lazy('immobilier:portail_accueil')

    def form_valid(self, form):
        messages.success(self.request, 'Votre mot de passe a été modifié avec succès.')
        # Marquer l'utilisateur comme ayant changé son mot de passe (via un champ du profil)
        # On utilise simplement last_login comme marqueur (si le mdp a déjà été changé)
        return super().form_valid(form)


# ===================================================================
# GESTION DES UTILISATEURS (Admin simplifié)
# ===================================================================
def gerer_compte_locataire(request, locataire_id):
    """Crée ou modifie le compte utilisateur d'un locataire, avec login auto."""
    if not request.user.is_staff:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return HttpResponseRedirect(reverse('immobilier:dashboard'))
    
    locataire = get_object_or_404(Locataire, pk=locataire_id)
    
    # Génération du login : prenom.nom (slugifié)
    import re
    base_username = re.sub(r'[^a-z0-9]', '', f"{locataire.prenom}.{locataire.nom}".lower().replace(' ', ''))
    username = base_username
    c = 1
    while User.objects.filter(username=username).exclude(email=locataire.email).exists():
        username = f"{base_username}{c}"
        c += 1

    if request.method == 'POST':
        action = request.POST.get('action', 'creer')
        
        # Génération mot de passe aléatoire
        import string, secrets
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        try:
            user = User.objects.get(email=locataire.email)
            if action == 'modifier':
                user.set_password(password)
                user.username = username
                user.save()
                messages.success(request, f'Compte modifié - Identifiant: {username} / Mot de passe: {password}')
            else:
                messages.info(request, f'Un compte existe déjà pour cet email.')
        except User.DoesNotExist:
            # Création
            if User.objects.filter(username=username).exists():
                username = f"{base_username}{User.objects.filter(username__startswith=base_username).count() + 1}"
            
            user = User.objects.create_user(
                username=username,
                email=locataire.email,
                password=password,
                first_name=locataire.prenom,
                last_name=locataire.nom
            )
            # Lier l'utilisateur au locataire
            locataire.user = user
            locataire.save(update_fields=['user'])
            
            # Groupe
            groupe_locataire, _ = Group.objects.get_or_create(name='Locataire')
            user.groups.add(groupe_locataire)
            
            messages.success(request, f'Compte créé - Identifiant: {username} / Mot de passe: {password}')
    
    return HttpResponseRedirect(reverse('immobilier:locataire_detail', kwargs={'pk': locataire_id}))


def creer_utilisateur_gestionnaire(request):
    """Crée un compte utilisateur gestionnaire (staff non-superuser)."""
    if not request.user.is_superuser:
        messages.error(request, 'Réservé aux super-administrateurs.')
        return HttpResponseRedirect(reverse('immobilier:dashboard'))
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True  # Accès à l'admin
            )
            groupe_gestionnaire, _ = Group.objects.get_or_create(name='Gestionnaire')
            user.groups.add(groupe_gestionnaire)
            messages.success(request, f'Gestionnaire {username} créé avec succès.')
        
        return HttpResponseRedirect(reverse('admin:index'))
    
    return render(request, 'immobilier/creer_gestionnaire.html')


