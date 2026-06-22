from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Proprietaire, BienImmobilier, Locataire, Garant,
    Bail, Paiement, Document, Intervention, PhotoBien,
    TypeBien, StatutBien
)


class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None, format='%Y-%m-%d'):
        super().__init__(attrs=attrs, format=format)


# ---------------------------------------------------------------------------
# Propriétaire
# ---------------------------------------------------------------------------
class ProprietaireForm(forms.ModelForm):
    class Meta:
        model = Proprietaire
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


# ---------------------------------------------------------------------------
# Bien Immobilier
# ---------------------------------------------------------------------------
class BienImmobilierForm(forms.ModelForm):
    class Meta:
        model = BienImmobilier
        exclude = ['date_creation', 'date_modification']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # Checkbox fields
        for f in ['meuble', 'ascenseur', 'balcon', 'parking', 'cave',
                   'jardin', 'piscine', 'interphone', 'gardien',
                   'acces_handicap', 'actif']:
            self.fields[f].widget.attrs.update({'class': 'form-check-input'})


class PhotoBienForm(forms.ModelForm):
    class Meta:
        model = PhotoBien
        fields = ['image', 'legende', 'est_principale']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['est_principale'].widget.attrs.update({'class': 'form-check-input'})


# ---------------------------------------------------------------------------
# Locataire
# ---------------------------------------------------------------------------
class LocataireForm(forms.ModelForm):
    class Meta:
        model = Locataire
        exclude = ['actif', 'date_creation', 'date_modification']
        widgets = {
            'date_naissance': DateInput(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class GarantForm(forms.ModelForm):
    class Meta:
        model = Garant
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


# ---------------------------------------------------------------------------
# Bail
# ---------------------------------------------------------------------------
class BailForm(forms.ModelForm):
    class Meta:
        model = Bail
        exclude = ['numero_contrat', 'date_creation', 'date_modification']
        widgets = {
            'date_debut': DateInput(),
            'date_fin': DateInput(),
            'date_prochaine_revision': DateInput(),
            'date_resiliation': DateInput(),
            'date_etat_lieux_entree': DateInput(),
            'date_etat_lieux_sortie': DateInput(),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'motif_resiliation': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        for f in ['tacite_reconduction', 'depot_garantie_encaisse',
                   'depot_garantie_restitué', 'assurance_locataire',
                   'assurance_proprietaire', 'clause_resolutoire',
                   'solidarite_colocataires']:
            self.fields[f].widget.attrs.update({'class': 'form-check-input'})
        # Remplacer actif/resiliation par un select unique
        statut_initial = 'ACTIF'
        if self.instance and self.instance.pk:
            if self.instance.resiliation:
                statut_initial = 'RESILIE'
            elif not self.instance.actif:
                statut_initial = 'TERMINE'
        self.fields['statut_bail'] = forms.ChoiceField(
            label=_('Statut du bail'),
            choices=[
                ('ACTIF', _('Actif — en cours')),
                ('RESILIE', _('Résilié')),
                ('TERMINE', _('Terminé (non résilié)')),
            ],
            initial=statut_initial,
            widget=forms.Select(attrs={'class': 'form-control'}),
        )
        # Masquer les champs originaux (ils seront gérés via clean)
        self.fields['actif'].widget = forms.HiddenInput()
        self.fields['resiliation'].widget = forms.HiddenInput()
        self.fields['actif'].required = False
        self.fields['resiliation'].required = False

    def clean(self):
        cleaned_data = super().clean()
        statut = cleaned_data.get('statut_bail', 'ACTIF')
        if statut == 'ACTIF':
            cleaned_data['actif'] = True
            cleaned_data['resiliation'] = False
        elif statut == 'RESILIE':
            cleaned_data['actif'] = False
            cleaned_data['resiliation'] = True
        elif statut == 'TERMINE':
            cleaned_data['actif'] = False
            cleaned_data['resiliation'] = False
        return cleaned_data


# ---------------------------------------------------------------------------
# Paiement
# ---------------------------------------------------------------------------
class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        exclude = ['quittance_generee', 'quittance_pdf', 'date_creation', 'date_modification']
        widgets = {
            'date_paiement': DateInput(),
            'date_periode_debut': DateInput(),
            'date_periode_fin': DateInput(),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


# ---------------------------------------------------------------------------
# Intervention
# ---------------------------------------------------------------------------
class InterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        exclude = ['date_soumission', 'date_creation', 'date_modification']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_planification': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


# ---------------------------------------------------------------------------
# Filtres / Recherche
# ---------------------------------------------------------------------------
class BienSearchForm(forms.Form):
    q = forms.CharField(label=_('Recherche'), required=False,
                        widget=forms.TextInput(
                            attrs={'class': 'form-control', 'placeholder': 'Titre, ville, adresse...'}))
    type_bien = forms.ChoiceField(label=_('Type'), required=False,
                                  choices=[('', '---')] + list(TypeBien.choices))
    statut = forms.ChoiceField(label=_('Statut'), required=False,
                               choices=[('', '---')] + list(StatutBien.choices))
    ville = forms.CharField(label=_('Ville'), required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}))
    prix_max = forms.DecimalField(label=_('Loyer max (€)'), required=False,
                                  widget=forms.NumberInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if not hasattr(self.fields[field].widget.attrs, '__contains__') or 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})



# ---------------------------------------------------------------------------
# Compte utilisateur locataire
# ---------------------------------------------------------------------------
class CompteLocataireForm(forms.Form):
    """Formulaire pour créer/modifier le compte utilisateur d'un locataire."""
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Laissé vide pour auto-génération'})
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '8 caractères minimum'})
    )
    password_confirm = forms.CharField(
        label=_('Confirmer le mot de passe'),
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise forms.ValidationError('Le mot de passe doit faire au moins 8 caractères.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('password_confirm')
        if password and password != confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned_data
