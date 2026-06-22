import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone(value):
    """Validate phone number format (French)."""
    pattern = r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Numéro de téléphone invalide. Format attendu: 01 23 45 67 89'),
        )


def validate_postal_code(value):
    """Validate French postal code."""
    pattern = r'^\d{5}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Code postal invalide. Format attendu: 5 chiffres'),
        )


def validate_siret(value):
    """Validate SIRET number."""
    if not re.match(r'^\d{14}$', value):
        raise ValidationError(
            _('Numéro SIRET invalide. Format attendu: 14 chiffres'),
        )


def validate_energy_rate(value):
    """Validate DPE energy rate (A to G)."""
    valid_rates = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    if value.upper() not in valid_rates:
        raise ValidationError(
            _('Classe énergétique invalide. Valeurs possibles: A, B, C, D, E, F, G'),
        )
