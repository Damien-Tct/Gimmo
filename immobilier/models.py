import os
import uuid
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

from .validators import validate_phone, validate_postal_code, validate_energy_rate


# ---------------------------------------------------------------------------
# Helpers / Upload paths
# ---------------------------------------------------------------------------
def photo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'photos/bien_{instance.bien.id}/{uuid.uuid4()}.{ext}'


def document_upload_path(instance, filename):
    return f'documents/{instance.categorie}/{uuid.uuid4()}_{filename}'


def locataire_document_path(instance, filename):
    return f'uploads/locataire_{instance.locataire.id}/{uuid.uuid4()}_{filename}'


# ---------------------------------------------------------------------------
# Type / Choix
# ---------------------------------------------------------------------------
class TypeBien(models.TextChoices):
    APPARTEMENT = 'APT', _('Appartement')
    MAISON = 'MSN', _('Maison')
    COMMERCIAL = 'COM', _('Local commercial')
    TERRAIN = 'TER', _('Terrain')
    STUDIO = 'STD', _('Studio')
    LOFT = 'LFT', _('Loft')
    PARKING = 'PKG', _('Parking / Garage')
    AUTRE = 'AUT', _('Autre')


class StatutBien(models.TextChoices):
    DISPONIBLE = 'DISP', _('Disponible')
    LOUE = 'LOUE', _('Loué')
    EN_TRAVAUX = 'TRAV', _('En travaux')
    VENDU = 'VEND', _('Vendu')
    RESERVE = 'RESV', _('Réservé')


class ModeChauffage(models.TextChoices):
    ELECTRIQUE = 'ELEC', _('Électrique')
    GAZ = 'GAZ', _('Gaz')
    FIOUL = 'FIOU', _('Fioul')
    BOIS = 'BOIS', _('Bois / granulés')
    POMPE_CHALEUR = 'PAC', _('Pompe à chaleur')
    SOLAIRE = 'SOL', _('Solaire')
    AUTRE = 'AUT', _('Autre')


class ModePaiement(models.TextChoices):
    VIREMENT = 'VIR', _('Virement bancaire')
    CHEQUE = 'CHQ', _('Chèque')
    ESPECES = 'ESP', _('Espèces')
    PRELEVEMENT = 'PRL', _('Prélèvement automatique')
    CARTE = 'CB', _('Carte bancaire')


class TypeDocument(models.TextChoices):
    BAIL = 'BAIL', _('Contrat de bail')
    ETAT_LIEUX = 'ETAT', _('État des lieux')
    DPE = 'DPE', _('Diagnostic Performance Énergétique')
    DIAGNOSTIC = 'DIAG', _('Diagnostic (gaz, électricité, etc.)')
    FACTURE = 'FACT', _('Facture')
    DEVIS = 'DEVI', _('Devis')
    ASSURANCE = 'ASSU', _("Assurance")
    REGLEMENT = 'REGL', _('Règlement de copropriété')
    FISCAL = 'FISC', _('Document fiscal')
    AUTRE = 'AUTR', _('Autre document')


class StatutIntervention(models.TextChoices):
    A_FAIRE = 'AFAI', _('À faire')
    EN_COURS = 'ENCO', _('En cours')
    TERMINE = 'TERM', _('Terminé')
    ANNULE = 'ANNU', _('Annulé')
    DIFFERE = 'DIFF', _('Différé')


class PrioriteIntervention(models.TextChoices):
    BASSE = 'BAS', _('Basse')
    MOYENNE = 'MOY', _('Moyenne')
    HAUTE = 'HAU', _('Haute')
    URGENTE = 'URG', _('Urgente')


# ---------------------------------------------------------------------------
# Propriétaire
# ---------------------------------------------------------------------------
class Proprietaire(models.Model):
    class TypePersonne(models.TextChoices):
        PHYSIQUE = 'PHY', _('Personne physique')
        MORALE = 'MOR', _('Personne morale (SCI, société)')

    type_personne = models.CharField(
        _('Type'), max_length=3, choices=TypePersonne.choices,
        default=TypePersonne.PHYSIQUE
    )
    # Personne physique
    civilite = models.CharField(_('Civilité'), max_length=4, choices=[
        ('M.', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')
    ], blank=True)
    nom = models.CharField(_('Nom'), max_length=100)
    prenom = models.CharField(_('Prénom'), max_length=100, blank=True)
    # Personne morale
    raison_sociale = models.CharField(_('Raison sociale'), max_length=200, blank=True)
    siret = models.CharField(_('SIRET'), max_length=14, blank=True)

    email = models.EmailField(_('Email'), max_length=254)
    telephone = models.CharField(_('Téléphone'), max_length=20, validators=[validate_phone])
    telephone_secondaire = models.CharField(_('Téléphone secondaire'), max_length=20, blank=True)

    adresse = models.CharField(_('Adresse'), max_length=255)
    code_postal = models.CharField(_('Code postal'), max_length=5, validators=[validate_postal_code])
    ville = models.CharField(_('Ville'), max_length=100)
    pays = models.CharField(_('Pays'), max_length=100, default='France')

    iban = models.CharField(_('IBAN'), max_length=34, blank=True, help_text='Pour les virements')
    bic = models.CharField(_('BIC'), max_length=11, blank=True)

    notes = models.TextField(_('Notes'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)
    actif = models.BooleanField(_('Actif'), default=True)

    class Meta:
        verbose_name = _('Propriétaire')
        verbose_name_plural = _('Propriétaires')
        ordering = ['nom', 'prenom']

    def __str__(self):
        if self.type_personne == 'MOR' and self.raison_sociale:
            return self.raison_sociale
        return f"{self.civilite} {self.nom} {self.prenom}".strip()

    def get_full_name(self):
        return str(self)

    def get_nb_biens(self):
        return self.biens.count()

    get_nb_biens.short_description = 'Nombre de biens'


# ---------------------------------------------------------------------------
# Bien Immobilier
# ---------------------------------------------------------------------------
class BienImmobilier(models.Model):
    proprietaire = models.ForeignKey(
        Proprietaire, verbose_name=_('Propriétaire'),
        on_delete=models.CASCADE, related_name='biens'
    )
    type_bien = models.CharField(
        _('Type de bien'), max_length=3, choices=TypeBien.choices
    )
    statut = models.CharField(
        _('Statut'), max_length=4, choices=StatutBien.choices,
        default=StatutBien.DISPONIBLE
    )
    titre = models.CharField(_('Titre / Description'), max_length=200)
    description = models.TextField(_('Description détaillée'), blank=True)

    # Adresse du bien
    adresse = models.CharField(_('Adresse'), max_length=255)
    complement_adresse = models.CharField(_("Complément d'adresse"), max_length=255, blank=True)
    code_postal = models.CharField(_('Code postal'), max_length=5, validators=[validate_postal_code])
    ville = models.CharField(_('Ville'), max_length=100)
    quartier = models.CharField(_('Quartier'), max_length=100, blank=True)
    pays = models.CharField(_('Pays'), max_length=100, default='France')

    # Caractéristiques
    surface_totale = models.DecimalField(
        _('Surface totale (m²)'), max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    surface_habitable = models.DecimalField(
        _('Surface habitable (m²)'), max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    nombre_pieces = models.PositiveSmallIntegerField(_('Nombre de pièces'))
    nombre_chambres = models.PositiveSmallIntegerField(_('Nombre de chambres'), default=0)
    etage = models.PositiveSmallIntegerField(_('Étage'), default=0)
    nombre_etages_total = models.PositiveSmallIntegerField(_("Nombre d'étages total"), default=1)

    # Détails
    meuble = models.BooleanField(_('Meublé'), default=False)
    mode_chauffage = models.CharField(
        _('Mode de chauffage'), max_length=4, choices=ModeChauffage.choices,
        default=ModeChauffage.ELECTRIQUE
    )
    classe_energie = models.CharField(
        _('Classe énergie (DPE)'), max_length=1, blank=True,
        validators=[validate_energy_rate]
    )
    classe_ges = models.CharField(
        _('Classe GES'), max_length=1, blank=True,
        validators=[validate_energy_rate]
    )
    annee_construction = models.PositiveSmallIntegerField(
        _('Année de construction'), null=True, blank=True
    )
    ascenseur = models.BooleanField(_('Ascenseur'), default=False)
    balcon = models.BooleanField(_('Balcon / Terrasse'), default=False)
    parking = models.BooleanField(_('Parking'), default=False)
    cave = models.BooleanField(_('Cave'), default=False)
    jardin = models.BooleanField(_('Jardin'), default=False)
    piscine = models.BooleanField(_('Piscine'), default=False)
    interphone = models.BooleanField(_('Interphone / Digicode'), default=False)
    gardien = models.BooleanField(_('Gardien'), default=False)
    acces_handicap = models.BooleanField(_('Accès handicapés'), default=False)

    # Loyer indicatif
    loyer_mensuel_indicatif = models.DecimalField(
        _('Loyer mensuel indicatif (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    charges_indicatives = models.DecimalField(
        _('Charges indicatives (€)'), max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    depot_garantie_mois = models.PositiveSmallIntegerField(
        _("Dépôt de garantie (nombre de mois de loyer)"), default=1
    )

    photo_principale = models.ImageField(
        _('Photo principale'), upload_to=photo_upload_path, blank=True, null=True
    )
    actif = models.BooleanField(_('Actif'), default=True)

    # Taxes / foncier
    taxe_fonciere = models.DecimalField(
        _('Taxe foncière (€/an)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )

    notes = models.TextField(_('Notes internes'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)

    class Meta:
        verbose_name = _('Bien immobilier')
        verbose_name_plural = _('Biens immobiliers')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_type_bien_display()} - {self.titre} ({self.ville})"

    def get_absolute_url(self):
        return reverse('bien_detail', args=[str(self.id)])

    def get_loyer_actuel(self):
        """Retourne le loyer actuel si le bien est loué."""
        bail_actif = self.baux.filter(actif=True, date_fin__gte=date.today()).first()
        if bail_actif:
            return bail_actif.loyer_mensuel
        return None

    def get_locataire_actuel(self):
        """Retourne le locataire actuel si le bien est loué."""
        bail_actif = self.baux.filter(actif=True, date_fin__gte=date.today()).first()
        if bail_actif:
            return bail_actif.locataire
        return None

    def get_photos(self):
        return self.photos.all()


# ---------------------------------------------------------------------------
# Photos du bien
# ---------------------------------------------------------------------------
class PhotoBien(models.Model):
    bien = models.ForeignKey(
        BienImmobilier, verbose_name=_('Bien'),
        on_delete=models.CASCADE, related_name='photos'
    )
    image = models.ImageField(_('Image'), upload_to=photo_upload_path)
    legende = models.CharField(_('Légende'), max_length=255, blank=True)
    est_principale = models.BooleanField(_('Photo principale'), default=False)
    date_upload = models.DateTimeField(_('Date'), auto_now_add=True)

    class Meta:
        verbose_name = _('Photo')
        verbose_name_plural = _('Photos')
        ordering = ['-est_principale', 'date_upload']

    def __str__(self):
        return f"Photo {self.bien.titre} - {self.legende or 'sans légende'}"


# ---------------------------------------------------------------------------
# Locataire
# ---------------------------------------------------------------------------
class Locataire(models.Model):
    civilite = models.CharField(_('Civilité'), max_length=4, choices=[
        ('M.', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')
    ])
    nom = models.CharField(_('Nom'), max_length=100)
    prenom = models.CharField(_('Prénom'), max_length=100)
    email = models.EmailField(_('Email'), max_length=254)
    telephone = models.CharField(_('Téléphone'), max_length=20, validators=[validate_phone])
    telephone_secondaire = models.CharField(_('Téléphone secondaire'), max_length=20, blank=True)
    
    user = models.OneToOneField(
        User, verbose_name=_('Utilisateur lié'),
        on_delete=models.SET_NULL, null=True, blank=True, related_name='locataire_profile'
    )

    date_naissance = models.DateField(_('Date de naissance'), null=True, blank=True)
    profession = models.CharField(_('Profession'), max_length=200, blank=True)
    employeur = models.CharField(_('Employeur'), max_length=200, blank=True)

    adresse = models.CharField(_('Adresse'), max_length=255)
    code_postal = models.CharField(_('Code postal'), max_length=5, validators=[validate_postal_code])
    ville = models.CharField(_('Ville'), max_length=100)
    pays = models.CharField(_('Pays'), max_length=100, default='France')

    # Pièces justificatives
    piece_identite = models.FileField(
        _("Pièce d'identité"), upload_to=locataire_document_path,
        blank=True, null=True
    )
    justificatif_domicile = models.FileField(
        _('Justificatif de domicile'), upload_to=locataire_document_path,
        blank=True, null=True
    )
    justificatif_revenus = models.FileField(
        _('Justificatif de revenus'), upload_to=locataire_document_path,
        blank=True, null=True
    )

    iban = models.CharField(_('IBAN'), max_length=34, blank=True)

    # Consentement RGPD
    consentement_rgpd = models.BooleanField(_('Consentement RGPD'), default=False)
    date_consentement_rgpd = models.DateTimeField(_('Date du consentement RGPD'), null=True, blank=True)

    notes = models.TextField(_('Notes'), blank=True)
    actif = models.BooleanField(_('Actif'), default=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)

    class Meta:
        verbose_name = _('Locataire')
        verbose_name_plural = _('Locataires')
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.civilite} {self.nom} {self.prenom}"

    def get_full_name(self):
        return f"{self.nom} {self.prenom}"

    def get_bail_actif(self):
        return self.baux.filter(actif=True, date_fin__gte=date.today()).first()

    def get_bien_actuel(self):
        bail = self.get_bail_actif()
        return bail.bien if bail else None

    @property
    def est_actif(self):
        """Un locataire est actif s'il a au moins un bail actif en cours."""
        return self.get_bail_actif() is not None


# ---------------------------------------------------------------------------
# Garant
# ---------------------------------------------------------------------------
class Garant(models.Model):
    locataire = models.ForeignKey(
        Locataire, verbose_name=_('Locataire'),
        on_delete=models.CASCADE, related_name='garants'
    )
    civilite = models.CharField(_('Civilité'), max_length=4, choices=[
        ('M.', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')
    ])
    nom = models.CharField(_('Nom'), max_length=100)
    prenom = models.CharField(_('Prénom'), max_length=100)
    email = models.EmailField(_('Email'), max_length=254)
    telephone = models.CharField(_('Téléphone'), max_length=20, validators=[validate_phone])
    adresse = models.CharField(_('Adresse'), max_length=255)
    code_postal = models.CharField(_('Code postal'), max_length=5, validators=[validate_postal_code])
    ville = models.CharField(_('Ville'), max_length=100)
    revenus_mensuels = models.DecimalField(
        _('Revenus mensuels (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    document = models.FileField(
        _('Document justificatif'), upload_to='uploads/garants/', blank=True
    )
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)

    class Meta:
        verbose_name = _('Garant')
        verbose_name_plural = _('Garants')

    def __str__(self):
        return f"{self.civilite} {self.nom} {self.prenom} - Garant de {self.locataire}"


# ---------------------------------------------------------------------------
# Bail (Contrat de location)
# ---------------------------------------------------------------------------
class Bail(models.Model):
    class TypeBail(models.TextChoices):
        VIDE = 'VIDE', _('Location vide')
        MEUBLE = 'MEUB', _('Location meublée')
        SAISONNIER = 'SAIS', _('Location saisonnière')
        COMMERCIAL = 'COMM', _('Bail commercial')
        PROFESSIONNEL = 'PROF', _('Bail professionnel')

    class ModalitePaiement(models.TextChoices):
        MENSUEL = 'MEN', _('Mensuel')
        TRIMESTRIEL = 'TRI', _('Trimestriel')
        SEMESTRIEL = 'SEM', _('Semestriel')
        ANNUEL = 'ANN', _('Annuel')

    numero_contrat = models.CharField(_('Numéro de contrat'), max_length=50, unique=True)
    bien = models.ForeignKey(
        BienImmobilier, verbose_name=_('Bien'),
        on_delete=models.CASCADE, related_name='baux'
    )
    locataire = models.ForeignKey(
        Locataire, verbose_name=_('Locataire'),
        on_delete=models.CASCADE, related_name='baux'
    )
    # Co-locataires éventuels (relation many-to-many simplifiée)
    colocataires = models.ManyToManyField(
        Locataire, verbose_name=_('Colocataires'),
        related_name='baux_colocation', blank=True
    )

    type_bail = models.CharField(
        _('Type de bail'), max_length=4, choices=TypeBail.choices,
        default=TypeBail.VIDE
    )

    date_debut = models.DateField(_('Date de début'))
    date_fin = models.DateField(_('Date de fin'))
    duree_mois = models.PositiveSmallIntegerField(_('Durée (mois)'), default=12)
    tacite_reconduction = models.BooleanField(_('Tacite reconduction'), default=True)
    preavis_mois = models.PositiveSmallIntegerField(_('Préavis (mois)'), default=3)

    # Aspects financiers
    loyer_mensuel = models.DecimalField(
        _('Loyer mensuel (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    charges_mensuelles = models.DecimalField(
        _('Charges mensuelles (€)'), max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    provision_charges = models.DecimalField(
        _('Provision sur charges (€)'), max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    depot_garantie = models.DecimalField(
        _('Dépôt de garantie (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    depot_garantie_encaisse = models.BooleanField(
        _('Dépôt de garantie encaissé'), default=False
    )
    depot_garantie_restitué = models.BooleanField(
        _('Dépôt de garantie restitué'), default=False
    )
    modalite_paiement = models.CharField(
        _('Modalité de paiement'), max_length=3, choices=ModalitePaiement.choices,
        default=ModalitePaiement.MENSUEL
    )
    jour_paiement = models.PositiveSmallIntegerField(
        _('Jour de paiement'), default=5,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )

    # Révision de loyer
    indice_revision = models.CharField(
        _("Indice de révision"), max_length=50,
        default='IRL (Indice de Référence des Loyers)'
    )
    date_prochaine_revision = models.DateField(_('Prochaine révision'), null=True, blank=True)
    montant_annuel_revision = models.DecimalField(
        _('Montant annuel de révision (%)'), max_digits=5, decimal_places=2,
        default=Decimal('0.00')
    )

    # État des lieux
    etat_lieux_entree = models.FileField(
        _("État des lieux d'entrée"), upload_to='documents/etat_lieux/', blank=True
    )
    etat_lieux_sortie = models.FileField(
        _("État des lieux de sortie"), upload_to='documents/etat_lieux/', blank=True
    )
    date_etat_lieux_entree = models.DateField(_("Date EDL d'entrée"), null=True, blank=True)
    date_etat_lieux_sortie = models.DateField(_("Date EDL de sortie"), null=True, blank=True)

    # Assurance
    assurance_locataire = models.BooleanField(_('Assurance locataire fournie'), default=False)
    assurance_proprietaire = models.BooleanField(_('Assurance propriétaire'), default=False)

    # Clauses
    clause_resolutoire = models.BooleanField(_('Clause résolutoire'), default=True)
    solidarite_colocataires = models.BooleanField(_('Solidarité colocataires'), default=True)

    actif = models.BooleanField(_('Actif'), default=True)
    resiliation = models.BooleanField(_('Résilié'), default=False)
    date_resiliation = models.DateField(_('Date de résiliation'), null=True, blank=True)
    motif_resiliation = models.TextField(_('Motif de résiliation'), blank=True)

    notes = models.TextField(_('Notes'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)

    class Meta:
        verbose_name = _('Bail / Contrat')
        verbose_name_plural = _('Baux / Contrats')
        ordering = ['-date_debut']

    def __str__(self):
        return f"Bail {self.numero_contrat} - {self.bien} / {self.locataire}"

    def get_absolute_url(self):
        return reverse('bail_detail', args=[str(self.id)])

    def loyer_total(self):
        return self.loyer_mensuel + self.charges_mensuelles

    def save(self, *args, **kwargs):
        if not self.numero_contrat:
            # Génération auto du numéro de contrat
            year = timezone.now().year
            count = Bail.objects.filter(date_creation__year=year).count() + 1
            self.numero_contrat = f"BAIL-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def est_en_cours(self):
        return self.actif and self.date_debut <= date.today() <= self.date_fin and not self.resiliation

    def reste_a_payer(self, mois=None, annee=None):
        """Calcule le montant restant dû pour un mois donné."""
        from django.db.models import Sum
        today = date.today()
        # Si le bail n'a pas encore commencé, rien n'est dû
        if self.date_debut > today:
            return Decimal('0.00')
        m = mois or today.month
        a = annee or today.year
        total_du = self.loyer_mensuel + self.charges_mensuelles
        total_paye = self.paiements.filter(
            date_paiement__month=m, date_paiement__year=a,
            statut__in=['VALID', 'EN_ATTENTE']
        ).aggregate(total=Sum('montant'))['total'] or 0
        return max(Decimal('0.00'), total_du - total_paye)


# ---------------------------------------------------------------------------
# Paiement / Quittance
# ---------------------------------------------------------------------------
class Paiement(models.Model):
    class StatutPaiement(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', _('En attente')
        VALIDE = 'VALID', _('Validé')
        EN_RETARD = 'RETARD', _('En retard')
        ANNULE = 'ANNULE', _('Annulé')

    bail = models.ForeignKey(
        Bail, verbose_name=_('Bail'),
        on_delete=models.CASCADE, related_name='paiements'
    )
    locataire = models.ForeignKey(
        Locataire, verbose_name=_('Locataire'),
        on_delete=models.SET_NULL, null=True, related_name='paiements'
    )
    montant = models.DecimalField(
        _('Montant (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    montant_charges = models.DecimalField(
        _('Montant charges (€)'), max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    mode_paiement = models.CharField(
        _('Mode de paiement'), max_length=3, choices=ModePaiement.choices,
        default=ModePaiement.VIREMENT
    )
    date_paiement = models.DateField(_('Date de paiement'), default=date.today)
    date_periode_debut = models.DateField(_('Début de période'))
    date_periode_fin = models.DateField(_('Fin de période'))
    reference = models.CharField(_('Référence'), max_length=100, blank=True)
    statut = models.CharField(
        _('Statut'), max_length=12, choices=StatutPaiement.choices,
        default=StatutPaiement.EN_ATTENTE
    )
    quittance_generee = models.BooleanField(_('Quittance générée'), default=False)
    quittance_pdf = models.FileField(
        _('Quittance PDF'), upload_to='quittances/', blank=True, null=True
    )
    notes = models.TextField(_('Notes'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)

    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-date_paiement', '-date_creation']

    def __str__(self):
        return f"Paiement {self.montant}€ - {self.bail} - {self.date_paiement}"

    def save(self, *args, **kwargs):
        if not self.locataire_id:
            self.locataire = self.bail.locataire
        super().save(*args, **kwargs)

    def est_impaye(self):
        return self.statut == 'EN_RETARD' or (self.statut == 'EN_ATTENTE' and self.date_paiement < date.today())


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
class Document(models.Model):
    bien = models.ForeignKey(
        BienImmobilier, verbose_name=_('Bien'),
        on_delete=models.CASCADE, related_name='documents', null=True, blank=True
    )
    proprietaire = models.ForeignKey(
        Proprietaire, verbose_name=_('Propriétaire'),
        on_delete=models.CASCADE, related_name='documents', null=True, blank=True
    )
    locataire = models.ForeignKey(
        Locataire, verbose_name=_('Locataire'),
        on_delete=models.CASCADE, related_name='documents', null=True, blank=True
    )
    bail = models.ForeignKey(
        Bail, verbose_name=_('Bail'),
        on_delete=models.CASCADE, related_name='documents', null=True, blank=True
    )
    categorie = models.CharField(
        _('Catégorie'), max_length=4, choices=TypeDocument.choices,
        default=TypeDocument.AUTRE
    )
    titre = models.CharField(_('Titre'), max_length=200)
    fichier = models.FileField(_('Fichier'), upload_to=document_upload_path)
    notes = models.TextField(_('Notes'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_categorie_display()} - {self.titre}"

    @property
    def extension(self):
        _, ext = os.path.splitext(self.fichier.name)
        return ext.lower() if ext else ''


# ---------------------------------------------------------------------------
# Intervention (Travaux / Réparations)
# ---------------------------------------------------------------------------
class Intervention(models.Model):
    bien = models.ForeignKey(
        BienImmobilier, verbose_name=_('Bien'),
        on_delete=models.CASCADE, related_name='interventions'
    )
    locataire = models.ForeignKey(
        Locataire, verbose_name=_('Locataire (demandeur)'),
        on_delete=models.SET_NULL, null=True, blank=True, related_name='interventions'
    )
    titre = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    statut = models.CharField(
        _('Statut'), max_length=4, choices=StatutIntervention.choices,
        default=StatutIntervention.A_FAIRE
    )
    priorite = models.CharField(
        _('Priorité'), max_length=3, choices=PrioriteIntervention.choices,
        default=PrioriteIntervention.MOYENNE
    )
    date_soumission = models.DateTimeField(_('Date de soumission'), auto_now_add=True)
    date_debut = models.DateTimeField(_('Date de début'), null=True, blank=True)
    date_fin = models.DateTimeField(_('Date de fin'), null=True, blank=True)
    date_planification = models.DateTimeField(_('Planifiée le'), null=True, blank=True)

    # Prestataire
    prestataire_nom = models.CharField(_('Nom du prestataire'), max_length=200, blank=True)
    prestataire_telephone = models.CharField(_('Téléphone prestataire'), max_length=20, blank=True)
    prestataire_email = models.EmailField(_('Email prestataire'), blank=True)

    # Coûts
    cout_estime = models.DecimalField(
        _('Coût estimé (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    cout_reel = models.DecimalField(
        _('Coût réel (€)'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))], default=0
    )
    devis = models.FileField(
        _('Devis'), upload_to='documents/devis/', blank=True
    )
    facture = models.FileField(
        _('Facture'), upload_to='documents/factures/', blank=True
    )

    notes = models.TextField(_('Notes internes'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('Dernière modification'), auto_now=True)

    class Meta:
        verbose_name = _('Intervention')
        verbose_name_plural = _('Interventions')
        ordering = ['-priorite', '-date_soumission']

    def __str__(self):
        return f"[{self.get_priorite_display()}] {self.titre} - {self.bien}"

    def get_absolute_url(self):
        return reverse('intervention_detail', args=[str(self.id)])
