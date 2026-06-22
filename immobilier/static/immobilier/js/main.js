/**
 * Script principal pour l'application de gestion immobilière
 */

document.addEventListener('DOMContentLoaded', function() {

    // Auto-fermeture des alertes après 5 secondes
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirmation avant suppression (alternative aux templates dédiés)
    document.querySelectorAll('[data-confirm]').forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || 'Êtes-vous sûr ?')) {
                e.preventDefault();
            }
        });
    });

    // Activation des tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) {
        return new bootstrap.Tooltip(el);
    });

    // Masquage/Affichage des champs conditionnels dans les formulaires
    function togglePersonneMorale() {
        const typeSelect = document.querySelector('[name="type_personne"]');
        if (typeSelect) {
            const isMorale = typeSelect.value === 'MOR';
            document.querySelectorAll('.field-raisociale, .field-siret').forEach(function(field) {
                field.style.display = isMorale ? 'block' : 'none';
            });
            document.querySelectorAll('.field-civilite, .field-prenom').forEach(function(field) {
                field.style.display = isMorale ? 'none' : 'block';
            });
        }
    }
    togglePersonneMorale();
    document.querySelector('[name="type_personne"]')?.addEventListener('change', togglePersonneMorale);

    // Recalcul automatique du bail : date_fin = date_debut + duree_mois
    const dateDebutInput = document.querySelector('[name="date_debut"]');
    const dureeInput = document.querySelector('[name="duree_mois"]');
    const dateFinInput = document.querySelector('[name="date_fin"]');

    function updateDateFin() {
        if (dateDebutInput && dureeInput && dateFinInput) {
            const dateDebut = new Date(dateDebutInput.value);
            const duree = parseInt(dureeInput.value, 10);
            if (dateDebut instanceof Date && !isNaN(dateDebut) && duree > 0) {
                const dateFin = new Date(dateDebut);
                dateFin.setMonth(dateFin.getMonth() + duree);
                dateFin.setDate(dateFin.getDate() - 1);
                dateFinInput.value = dateFin.toISOString().split('T')[0];
            }
        }
    }
    dateDebutInput?.addEventListener('change', updateDateFin);
    dureeInput?.addEventListener('change', updateDateFin);

    // Confirmation par email duplicata check
    const emailInput = document.querySelector('[name="email"]');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            if (this.value) {
                // On pourrait faire une vérification AJAX ici
                this.classList.remove('is-invalid');
            }
        });
    }

    // Formatage des champs téléphone (espacement automatique)
    const phoneInputs = document.querySelectorAll('[name="telephone"], [name="telephone_secondaire"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 10) value = value.slice(0, 10);
            let formatted = '';
            for (let i = 0; i < value.length; i += 2) {
                formatted += value.slice(i, i + 2) + ' ';
            }
            this.value = formatted.trim();
        });
    });

    // Amélioration des selects avec recherche (si beaucoup d'options)
    const largeSelects = document.querySelectorAll('select[data-searchable]');
    largeSelects.forEach(function(select) {
        // On pourrait intégrer Select2 ou Choice.js ici
        select.classList.add('form-select');
    });

    console.log('Application Gestion Immobilière chargée.');
});
