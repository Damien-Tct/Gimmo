"""
Vues de l'application de gestion immobilière.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django_filters.views import FilterView

from .models import (
    Proprietaire, BienImmobilier, PhotoBien, Locataire, Garant,
    Bail, Paiement, Document, Intervention
)
from .forms import (
    ProprietaireForm, BienImmobilierForm, PhotoBienForm,
    LocataireForm, GarantForm, BailForm, PaiementForm,
    DocumentForm, InterventionForm
)
from .filters import (
    ProprietaireFilter, BienImmobilierFilter, LocataireFilter,
    BailFilter, PaiementFilter, InterventionFilter
)
from .utils import get_dashboard_stats, generate_graphiques, generer_quittance_pdf, generer_appel_loyer_pdf


# ===================================================================
# DASHBOARD
# ===================================================================
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'immobilier/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = get_dashboard_stats()
        context['graphs'] = generate_graphiques()

        # Derniers paiements
        context['derniers_paiements'] = Paiement.objects.select_related(
            'bail', 'locataire'
        ).order_by('-date_creation')[:10]

        # Dernières interventions
        context['dernieres_interventions'] = Intervention.objects.select_related(
            'bien'
        ).order_by('-date_soumission')[:5]

        # Baux expirant bientôt
        context['baux_expirant'] = Bail.objects.filter(
            actif=True, resiliation=False,
            date_fin__gte=date.today(),
            date_fin__lte=date.today() + timedelta(days=90)
        ).select_related('bien', 'locataire').order_by('date_fin')[:5]

        # Impayés
        context['impayes'] = Paiement.objects.filter(statut='EN_RETARD').select_related(
            'bail', 'locataire'
        ).order_by('-date_paiement')[:5]

        return context


# ===================================================================
# BIENS IMMOBILIERS
# ===================================================================
class BienListView(LoginRequiredMixin, FilterView):
    model = BienImmobilier
    filterset_class = BienImmobilierFilter
    template_name = 'immobilier/bien_list.html'
    context_object_name = 'biens'
    paginate_by = 12

    def get_queryset(self):
        return BienImmobilier.objects.select_related('proprietaire').all()


class BienDetailView(LoginRequiredMixin, DetailView):
    model = BienImmobilier
    template_name = 'immobilier/bien_detail.html'
    context_object_name = 'bien'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bien = self.get_object()
        context['baux'] = Bail.objects.filter(bien=bien).select_related('locataire').order_by('-date_debut')
        context['photos'] = bien.photos.all()
        context['documents'] = Document.objects.filter(bien=bien).order_by('-date_creation')
        context['interventions'] = Intervention.objects.filter(bien=bien).order_by('-date_soumission')
        context['paiements'] = Paiement.objects.filter(
            bail__bien=bien
        ).select_related('bail', 'locataire').order_by('-date_paiement')[:10]
        return context


class BienCreateView(LoginRequiredMixin, CreateView):
    model = BienImmobilier
    form_class = BienImmobilierForm
    template_name = 'immobilier/bien_form.html'
    success_url = reverse_lazy('immobilier:bien_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bien immobilier créé avec succès.')
        return super().form_valid(form)


class BienUpdateView(LoginRequiredMixin, UpdateView):
    model = BienImmobilier
    form_class = BienImmobilierForm
    template_name = 'immobilier/bien_form.html'
    context_object_name = 'bien'

    def get_success_url(self):
        return reverse_lazy('immobilier:bien_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Bien immobilier modifié avec succès.')
        return super().form_valid(form)


class BienDeleteView(LoginRequiredMixin, DeleteView):
    model = BienImmobilier
    template_name = 'immobilier/bien_confirm_delete.html'
    success_url = reverse_lazy('immobilier:bien_list')
    context_object_name = 'bien'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Bien immobilier supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class PhotoBienCreateView(LoginRequiredMixin, CreateView):
    model = PhotoBien
    form_class = PhotoBienForm
    template_name = 'immobilier/photo_form.html'

    def form_valid(self, form):
        bien = get_object_or_404(BienImmobilier, pk=self.kwargs['pk'])
        form.instance.bien = bien
        messages.success(self.request, 'Photo ajoutée avec succès.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('immobilier:bien_detail', kwargs={'pk': self.kwargs['pk']})


# ===================================================================
# PROPRIÉTAIRES
# ===================================================================
class ProprietaireListView(LoginRequiredMixin, FilterView):
    model = Proprietaire
    filterset_class = ProprietaireFilter
    template_name = 'immobilier/proprietaire_list.html'
    context_object_name = 'proprietaires'
    paginate_by = 20


class ProprietaireDetailView(LoginRequiredMixin, DetailView):
    model = Proprietaire
    template_name = 'immobilier/proprietaire_detail.html'
    context_object_name = 'proprietaire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prop = self.get_object()
        context['biens'] = BienImmobilier.objects.filter(proprietaire=prop).select_related()
        context['documents'] = Document.objects.filter(proprietaire=prop).order_by('-date_creation')
        # Revenus totaux
        revenus = Paiement.objects.filter(
            bail__bien__proprietaire=prop,
            statut='VALID'
        ).aggregate(total=Sum('montant'))
        context['revenus_total'] = revenus['total'] or 0
        return context


class ProprietaireCreateView(LoginRequiredMixin, CreateView):
    model = Proprietaire
    form_class = ProprietaireForm
    template_name = 'immobilier/proprietaire_form.html'
    success_url = reverse_lazy('immobilier:proprietaire_list')

    def form_valid(self, form):
        messages.success(self.request, 'Propriétaire créé avec succès.')
        return super().form_valid(form)


class ProprietaireUpdateView(LoginRequiredMixin, UpdateView):
    model = Proprietaire
    form_class = ProprietaireForm
    template_name = 'immobilier/proprietaire_form.html'
    context_object_name = 'proprietaire'

    def get_success_url(self):
        return reverse_lazy('immobilier:proprietaire_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Propriétaire modifié avec succès.')
        return super().form_valid(form)


class ProprietaireDeleteView(LoginRequiredMixin, DeleteView):
    model = Proprietaire
    template_name = 'immobilier/proprietaire_confirm_delete.html'
    success_url = reverse_lazy('immobilier:proprietaire_list')
    context_object_name = 'proprietaire'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Propriétaire supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


# ===================================================================
# LOCATAIRES
# ===================================================================
class LocataireListView(LoginRequiredMixin, FilterView):
    model = Locataire
    filterset_class = LocataireFilter
    template_name = 'immobilier/locataire_list.html'
    context_object_name = 'locataires'
    paginate_by = 20


class LocataireDetailView(LoginRequiredMixin, DetailView):
    model = Locataire
    template_name = 'immobilier/locataire_detail.html'
    context_object_name = 'locataire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loc = self.get_object()
        context['baux'] = Bail.objects.filter(
            Q(locataire=loc) | Q(colocataires=loc)
        ).select_related('bien').order_by('-date_debut')
        context['garants'] = Garant.objects.filter(locataire=loc)
        context['documents'] = Document.objects.filter(locataire=loc).order_by('-date_creation')
        context['paiements'] = Paiement.objects.filter(locataire=loc).select_related(
            'bail'
        ).order_by('-date_paiement')[:10]
        context['interventions'] = Intervention.objects.filter(locataire=loc).order_by('-date_soumission')
        # Compte utilisateur lié
        try:
            context['user_compte'] = User.objects.get(email=loc.email)
        except User.DoesNotExist:
            context['user_compte'] = None
        return context


class LocataireCreateView(LoginRequiredMixin, CreateView):
    model = Locataire
    form_class = LocataireForm
    template_name = 'immobilier/locataire_form.html'
    success_url = reverse_lazy('immobilier:locataire_list')

    def form_valid(self, form):
        messages.success(self.request, 'Locataire créé avec succès.')
        return super().form_valid(form)


class LocataireUpdateView(LoginRequiredMixin, UpdateView):
    model = Locataire
    form_class = LocataireForm
    template_name = 'immobilier/locataire_form.html'
    context_object_name = 'locataire'

    def get_success_url(self):
        return reverse_lazy('immobilier:locataire_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Locataire modifié avec succès.')
        return super().form_valid(form)


class LocataireDeleteView(LoginRequiredMixin, DeleteView):
    model = Locataire
    template_name = 'immobilier/locataire_confirm_delete.html'
    success_url = reverse_lazy('immobilier:locataire_list')
    context_object_name = 'locataire'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Locataire supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class GarantCreateView(LoginRequiredMixin, CreateView):
    model = Garant
    form_class = GarantForm
    template_name = 'immobilier/garant_form.html'

    def form_valid(self, form):
        locataire = get_object_or_404(Locataire, pk=self.kwargs['pk'])
        form.instance.locataire = locataire
        messages.success(self.request, 'Garant ajouté avec succès.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('immobilier:locataire_detail', kwargs={'pk': self.kwargs['pk']})


# ===================================================================
# BAUX
# ===================================================================
class BailListView(LoginRequiredMixin, FilterView):
    model = Bail
    filterset_class = BailFilter
    template_name = 'immobilier/bail_list.html'
    context_object_name = 'baux'
    paginate_by = 20

    def get_queryset(self):
        return Bail.objects.select_related('bien', 'locataire').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date
        context['today'] = date.today()
        return context


class BailDetailView(LoginRequiredMixin, DetailView):
    model = Bail
    template_name = 'immobilier/bail_detail.html'
    context_object_name = 'bail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bail = self.get_object()
        context['paiements'] = Paiement.objects.filter(bail=bail).order_by('-date_paiement')
        context['documents'] = Document.objects.filter(bail=bail).order_by('-date_creation')
        context['appels_loyers'] = Document.objects.filter(
            bail=bail, titre__startswith='Appel de loyer'
        ).order_by('-date_creation')
        # Calcul du montant total perçu
        total_percu = Paiement.objects.filter(bail=bail, statut='VALID').aggregate(
            total=Sum('montant')
        )
        context['total_percu'] = total_percu['total'] or 0
        context['solde_attendu'] = max(0, (bail.loyer_mensuel + bail.charges_mensuelles) * (
            (date.today() - bail.date_debut).days // 30
        ))
        return context


class BailCreateView(LoginRequiredMixin, CreateView):
    model = Bail
    form_class = BailForm
    template_name = 'immobilier/bail_form.html'
    success_url = reverse_lazy('immobilier:bail_list')

    def get_initial(self):
        initial = super().get_initial()
        # Pré-remplir la durée et les dates si bail standard
        if 'bien' in self.request.GET:
            try:
                bien = BienImmobilier.objects.get(pk=self.request.GET['bien'])
                initial['bien'] = bien
                if bien.meuble:
                    initial['type_bail'] = 'MEUB'
                    initial['duree_mois'] = 12
                else:
                    initial['type_bail'] = 'VIDE'
                    initial['duree_mois'] = 36
            except BienImmobilier.DoesNotExist:
                pass
        if 'locataire' in self.request.GET:
            try:
                initial['locataire'] = Locataire.objects.get(pk=self.request.GET['locataire'])
            except Locataire.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Bail créé avec succès.')
        return super().form_valid(form)


class BailUpdateView(LoginRequiredMixin, UpdateView):
    model = Bail
    form_class = BailForm
    template_name = 'immobilier/bail_form.html'
    context_object_name = 'bail'

    def get_success_url(self):
        return reverse_lazy('immobilier:bail_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Bail modifié avec succès.')
        return super().form_valid(form)


class BailDeleteView(LoginRequiredMixin, DeleteView):
    model = Bail
    template_name = 'immobilier/bail_confirm_delete.html'
    success_url = reverse_lazy('immobilier:bail_list')
    context_object_name = 'bail'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Bail supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


# ===================================================================
# PAIEMENTS
# ===================================================================
class PaiementListView(LoginRequiredMixin, FilterView):
    model = Paiement
    filterset_class = PaiementFilter
    template_name = 'immobilier/paiement_list.html'
    context_object_name = 'paiements'
    paginate_by = 20

    def get_queryset(self):
        return Paiement.objects.select_related('bail', 'locataire').all()


class PaiementDeleteView(LoginRequiredMixin, DeleteView):
    model = Paiement
    template_name = 'immobilier/paiement_confirm_delete.html'
    context_object_name = 'paiement'

    def get_success_url(self):
        # Rediriger vers la page du bail associé, ou la liste des paiements
        if hasattr(self, 'bail_pk') and self.bail_pk:
            return reverse_lazy('immobilier:bail_detail', kwargs={'pk': self.bail_pk})
        return reverse_lazy('immobilier:paiement_list')

    def delete(self, request, *args, **kwargs):
        paiement = self.get_object()
        self.bail_pk = paiement.bail.pk if paiement.bail else None
        messages.success(request, 'Paiement supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class PaiementCreateView(LoginRequiredMixin, CreateView):
    model = Paiement
    form_class = PaiementForm
    template_name = 'immobilier/paiement_form.html'

    def get_initial(self):
        initial = super().get_initial()
        bail = get_object_or_404(Bail, pk=self.kwargs['pk'])
        initial['bail'] = bail
        initial['locataire'] = bail.locataire
        initial['montant'] = bail.loyer_mensuel
        initial['montant_charges'] = bail.charges_mensuelles
        initial['date_periode_debut'] = date.today().replace(day=1)
        # Fin de mois
        import calendar
        last_day = calendar.monthrange(date.today().year, date.today().month)[1]
        initial['date_periode_fin'] = date.today().replace(day=last_day)
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Paiement enregistré avec succès.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('immobilier:bail_detail', kwargs={'pk': self.kwargs['pk']})


def generate_quittance(request, pk):
    """Vue pour générer une quittance de loyer PDF et valider le paiement."""
    paiement = get_object_or_404(Paiement, pk=pk)
    try:
        filepath = generer_quittance_pdf(paiement)
        # Valider le paiement lors de la génération de la quittance
        paiement.statut = 'VALID'
        paiement.save(update_fields=['statut'])
        messages.success(request, 'Quittance générée et paiement validé avec succès.')
        return HttpResponseRedirect(reverse('immobilier:paiement_list'))
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération de la quittance : {str(e)}')
        return HttpResponseRedirect(reverse('immobilier:paiement_list'))


def generate_appel_loyer(request, pk):
    """Vue pour générer un appel de loyer (perception de loyer) PDF."""
    from datetime import date
    bail = get_object_or_404(Bail, pk=pk)
    mois = request.GET.get('mois')
    annee = request.GET.get('annee')
    try:
        mois = int(mois) if mois else date.today().month
        annee = int(annee) if annee else date.today().year
        filepath = generer_appel_loyer_pdf(bail, mois=mois, annee=annee)
        messages.success(request, f"Appel de loyer généré pour {mois:02d}/{annee}.")
        return HttpResponseRedirect(reverse('immobilier:bail_detail', kwargs={'pk': pk}))
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération : {str(e)}')
        return HttpResponseRedirect(reverse('immobilier:bail_detail', kwargs={'pk': pk}))


# ===================================================================
# DOCUMENTS
# ===================================================================
class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'immobilier/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = Document.objects.all().order_by('-date_creation')
        # Filtre par catégorie
        cat = self.request.GET.get('categorie')
        if cat:
            qs = qs.filter(categorie=cat)
        # Recherche
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(titre__icontains=q) |
                Q(notes__icontains=q)
            )
        return qs.select_related('bien', 'proprietaire', 'locataire')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorie_courante'] = self.request.GET.get('categorie', '')
        context['recherche'] = self.request.GET.get('q', '')
        context['doc_categories'] = Document._meta.get_field('categorie').choices
        return context


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'immobilier/document_form.html'
    success_url = reverse_lazy('immobilier:document_list')

    def get_initial(self):
        initial = super().get_initial()
        if 'bien' in self.request.GET:
            try:
                initial['bien'] = BienImmobilier.objects.get(pk=self.request.GET['bien'])
            except BienImmobilier.DoesNotExist:
                pass
        if 'proprietaire' in self.request.GET:
            try:
                initial['proprietaire'] = Proprietaire.objects.get(pk=self.request.GET['proprietaire'])
            except Proprietaire.DoesNotExist:
                pass
        if 'locataire' in self.request.GET:
            try:
                initial['locataire'] = Locataire.objects.get(pk=self.request.GET['locataire'])
            except Locataire.DoesNotExist:
                pass
        if 'bail' in self.request.GET:
            try:
                initial['bail'] = Bail.objects.get(pk=self.request.GET['bail'])
            except Bail.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Document ajouté avec succès.')
        return super().form_valid(form)


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    template_name = 'immobilier/document_confirm_delete.html'
    success_url = reverse_lazy('immobilier:document_list')
    context_object_name = 'document'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Document supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


# ===================================================================
# INTERVENTIONS
# ===================================================================
class InterventionListView(LoginRequiredMixin, FilterView):
    model = Intervention
    filterset_class = InterventionFilter
    template_name = 'immobilier/intervention_list.html'
    context_object_name = 'interventions'
    paginate_by = 20

    def get_queryset(self):
        return Intervention.objects.select_related('bien', 'locataire').all()


class InterventionDetailView(LoginRequiredMixin, DetailView):
    model = Intervention
    template_name = 'immobilier/intervention_detail.html'
    context_object_name = 'intervention'


class InterventionCreateView(LoginRequiredMixin, CreateView):
    model = Intervention
    form_class = InterventionForm
    template_name = 'immobilier/intervention_form.html'
    success_url = reverse_lazy('immobilier:intervention_list')

    def get_initial(self):
        initial = super().get_initial()
        if 'bien' in self.request.GET:
            try:
                initial['bien'] = BienImmobilier.objects.get(pk=self.request.GET['bien'])
            except BienImmobilier.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Intervention créée avec succès.')
        return super().form_valid(form)


class InterventionUpdateView(LoginRequiredMixin, UpdateView):
    model = Intervention
    form_class = InterventionForm
    template_name = 'immobilier/intervention_form.html'
    context_object_name = 'intervention'

    def get_success_url(self):
        return reverse_lazy('immobilier:intervention_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Intervention modifiée avec succès.')
        return super().form_valid(form)


class InterventionDeleteView(LoginRequiredMixin, DeleteView):
    model = Intervention
    template_name = 'immobilier/intervention_confirm_delete.html'
    success_url = reverse_lazy('immobilier:intervention_list')
    context_object_name = 'intervention'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Intervention supprimée avec succès.')
        return super().delete(request, *args, **kwargs)


# ===================================================================
# APPELS DE LOYER (Gestion groupée)
# ===================================================================
class AppelsLoyersView(LoginRequiredMixin, TemplateView):
    """Page de gestion des appels de loyer avec sélection multiple de baux."""
    template_name = 'immobilier/appels_loyers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Baux actifs avec locataire
        baux = Bail.objects.filter(
            actif=True, resiliation=False
        ).select_related('bien', 'locataire').order_by('bien__titre')
        
        from datetime import date
        today = date.today()
        
        # Ajouter le dernier appel de loyer et le total pour chaque bail
        from .models import Document
        for bail in baux:
            dernier = Document.objects.filter(
                bail=bail, titre__startswith='Appel de loyer'
            ).order_by('-date_creation').first()
            bail.dernier_appel = dernier.date_creation if dernier else None
            bail.loyer_total = (bail.loyer_mensuel or 0) + (bail.charges_mensuelles or 0)
            # Vérifier si le bail est en cours
            bail.est_en_cours = (
                bail.date_debut and bail.date_fin and
                bail.date_debut <= today and bail.date_fin >= today
            )
        
        context['baux_actifs'] = baux
        
        # Appels déjà générés
        context['appels'] = Document.objects.filter(
            titre__startswith='Appel de loyer'
        ).select_related('bien', 'locataire').order_by('-date_creation')[:50]
        
        # Mois et années pour le formulaire
        from datetime import date
        today = date.today()
        mois_fr = [
            {'valeur': 1, 'label': 'Janvier'},
            {'valeur': 2, 'label': 'Février'},
            {'valeur': 3, 'label': 'Mars'},
            {'valeur': 4, 'label': 'Avril'},
            {'valeur': 5, 'label': 'Mai'},
            {'valeur': 6, 'label': 'Juin'},
            {'valeur': 7, 'label': 'Juillet'},
            {'valeur': 8, 'label': 'Août'},
            {'valeur': 9, 'label': 'Septembre'},
            {'valeur': 10, 'label': 'Octobre'},
            {'valeur': 11, 'label': 'Novembre'},
            {'valeur': 12, 'label': 'Décembre'},
        ]
        for m in mois_fr:
            m['defaut'] = (m['valeur'] == today.month)
        context['mois_list'] = mois_fr
        context['annees'] = range(today.year - 2, today.year + 2)
        context['annee_courante'] = today.year
        
        return context


def generer_appels_loyers_masse(request):
    """Génère les appels de loyer pour plusieurs baux sélectionnés."""
    from datetime import date
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('immobilier:appels_loyers'))
    
    baux_ids = request.POST.getlist('baux')
    mois = int(request.POST.get('mois', date.today().month))
    annee = int(request.POST.get('annee', date.today().year))
    
    if not baux_ids:
        messages.error(request, 'Veuillez sélectionner au moins un bail.')
        return HttpResponseRedirect(reverse('immobilier:appels_loyers'))
    
    baux = Bail.objects.filter(pk__in=baux_ids, actif=True, resiliation=False)
    
    succes = 0
    erreurs = 0
    
    for bail in baux:
        try:
            generer_appel_loyer_pdf(bail, mois=mois, annee=annee)
            succes += 1
        except Exception as e:
            erreurs += 1
    
    if succes > 0:
        messages.success(request, f'{succes} appel(s) de loyer généré(s) avec succès pour {mois:02d}/{annee}.')
    if erreurs > 0:
        messages.error(request, f'{erreurs} erreur(s) lors de la génération.')
    
    return HttpResponseRedirect(reverse('immobilier:appels_loyers'))


def supprimer_appel_loyer(request, pk):
    """Supprime un appel de loyer (Document) et le paiement en attente associé."""
    from datetime import date
    from .models import Document, Paiement

    doc = get_object_or_404(Document, pk=pk, titre__startswith='Appel de loyer')
    bail = doc.bail
    locataire = doc.locataire

    # Chercher le paiement en attente associé (même période)
    import re
    match = re.search(r'(\d{4})$', doc.titre)  # ex: "Appel de loyer - Janvier 2025" → "2025"
    if match:
        annee = int(match.group(1))
        # Trouver tous les paiements en attente pour ce bail/période
        paiements = Paiement.objects.filter(
            bail=bail,
            locataire=locataire,
            statut='EN_ATTENTE',
            date_periode_debut__year=annee,
        )
        for p in paiements:
            p.delete()

    doc.delete()
    messages.success(request, 'Appel de loyer supprimé avec succès.')
    return HttpResponseRedirect(reverse('immobilier:appels_loyers'))


# ===================================================================
# RGPD
# ===================================================================
class RgpdView(TemplateView):
    template_name = 'immobilier/rgpd.html'
