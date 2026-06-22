"""
Utilitaires pour l'application immobilière.
"""
import io
import os
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils import timezone

# ReportLab pour PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generer_quittance_pdf(paiement):
    """
    Génère une quittance de loyer au format PDF pour un paiement donné.
    Retourne le chemin du fichier PDF.
    """
    bail = paiement.bail
    bien = bail.bien
    proprietaire = bien.proprietaire
    locataire = paiement.locataire

    # Nom du fichier
    mois = paiement.date_periode_debut.strftime('%Y_%m')  # format numérique pour fichier
    filename = f"quittance_{bail.numero_contrat}_{mois}.pdf"
    dir_path = os.path.join(settings.MEDIA_ROOT, 'quittances')
    os.makedirs(dir_path, exist_ok=True)
    filepath = os.path.join(dir_path, filename)

    # Création du document
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm
    )

    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'TitleCustom', parent=styles['Title'],
        fontSize=18, spaceAfter=20, alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    subtitle_style = ParagraphStyle(
        'SubtitleCustom', parent=styles['Normal'],
        fontSize=12, spaceAfter=10, alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    normal_style = ParagraphStyle(
        'NormalCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6
    )
    bold_style = ParagraphStyle(
        'BoldCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    right_style = ParagraphStyle(
        'RightCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6, alignment=TA_RIGHT
    )

    elements = []

    # En-tête
    elements.append(Paragraph("QUITTANCE DE LOYER", title_style))
    elements.append(Paragraph(f"N° {paiement.id} - {date.today().strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(Spacer(1, 20))

    # Informations
    elements.append(Paragraph(
        f"<b>Période concernée :</b> du {paiement.date_periode_debut.strftime('%d/%m/%Y')} "
        f"au {paiement.date_periode_fin.strftime('%d/%m/%Y')}",
        normal_style
    ))
    elements.append(Spacer(1, 15))

    # Tableau du bailleur
    elements.append(Paragraph("<b>LE BAILLEUR</b>", bold_style))
    elements.append(Paragraph(
        f"{proprietaire.get_full_name()}<br/>"
        f"{proprietaire.adresse}<br/>"
        f"{proprietaire.code_postal} {proprietaire.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 10))

    # Tableau du locataire
    elements.append(Paragraph("<b>LE LOCATAIRE</b>", bold_style))
    elements.append(Paragraph(
        f"{locataire.get_full_name()}<br/>"
        f"{locataire.adresse}<br/>"
        f"{locataire.code_postal} {locataire.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 10))

    # Adresse du logement
    elements.append(Paragraph("<b>LOGEMENT CONCERNÉ</b>", bold_style))
    elements.append(Paragraph(
        f"{bien.get_type_bien_display()} - {bien.titre}<br/>"
        f"{bien.adresse}<br/>"
        f"{bien.code_postal} {bien.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 15))

    # Détail des sommes
    table_style_normal = ParagraphStyle('TableCellNormal', parent=normal_style, fontSize=10, alignment=TA_CENTER)
    table_style_bold = ParagraphStyle('TableCellBold', parent=normal_style, fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')
    table_style_header = ParagraphStyle('TableCellHeader', parent=normal_style, fontSize=11, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.white)
    
    data = [
        [Paragraph('Désignation', table_style_header), Paragraph('Montant', table_style_header)],
        [Paragraph('Loyer mensuel', table_style_normal), Paragraph(f"{paiement.montant:.2f} €", table_style_normal)],
        [Paragraph('Charges', table_style_normal), Paragraph(f"{paiement.montant_charges:.2f} €", table_style_normal)],
        [Paragraph('<b>Total payé</b>', table_style_bold), Paragraph(f"<b>{paiement.montant + paiement.montant_charges:.2f} €</b>", table_style_bold)],
    ]
    
    table = Table(data, colWidths=[12*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (1, -2), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15))

    # Mode de paiement
    elements.append(Paragraph(
        f"<b>Mode de paiement :</b> {paiement.get_mode_paiement_display()}",
        normal_style
    ))
    if paiement.reference:
        elements.append(Paragraph(
            f"<b>Référence :</b> {paiement.reference}",
            normal_style
        ))
    elements.append(Spacer(1, 10))

    # Mention légale
    elements.append(Paragraph(
        "<i>Cette quittance annule et remplace tout reçu précédemment délivré pour la même période. "
        "Elle est à conserver par le locataire pendant 3 ans.</i>",
        ParagraphStyle('LegalStyle', parent=normal_style, fontSize=8,
                       textColor=colors.HexColor('#95a5a6'))
    ))
    elements.append(Spacer(1, 20))

    # Signature
    elements.append(Paragraph(
        f"Fait à {proprietaire.ville}, le {date.today().strftime('%d/%m/%Y')}",
        right_style
    ))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Signature du bailleur",
        right_style
    ))

    # Génération
    doc.build(elements)

    # Sauvegarde dans le modèle
    paiement.quittance_pdf.name = f'quittances/{filename}'
    paiement.quittance_generee = True
    paiement.save()

    return filepath



def generer_appel_loyer_pdf(bail, mois=None, annee=None):
    """
    Génère un avis d'échéance / appel de loyer (perception de loyer) PDF
    pour un bail donné, pour un mois/année spécifique ou le mois en cours.
    Retourne le chemin du fichier PDF.
    """
    from datetime import date
    from django.conf import settings
    import os
    
    mois_fr = {1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
               5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
               9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'}
    
    bien = bail.bien
    proprietaire = bien.proprietaire
    locataire = bail.locataire
    
    if mois is None:
        mois = date.today().month
    if annee is None:
        annee = date.today().year
    
    # Nom du fichier
    filename = f"appel_loyer_{bail.numero_contrat}_{annee}_{mois:02d}.pdf"
    dir_path = os.path.join(settings.MEDIA_ROOT, 'appels_loyers')
    os.makedirs(dir_path, exist_ok=True)
    filepath = os.path.join(dir_path, filename)
    
    # Création du document
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleCustom', parent=styles['Title'],
        fontSize=18, spaceAfter=20, alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    subtitle_style = ParagraphStyle(
        'SubtitleCustom', parent=styles['Normal'],
        fontSize=12, spaceAfter=10, alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    normal_style = ParagraphStyle(
        'NormalCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6
    )
    bold_style = ParagraphStyle(
        'BoldCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    right_style = ParagraphStyle(
        'RightCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6, alignment=TA_RIGHT
    )

    elements = []

    # En-tête
    elements.append(Paragraph("AVIS D'ÉCHÉANCE", title_style))
    elements.append(Paragraph(
        f"Mois de {mois_fr[mois]} {annee}",
        subtitle_style
    ))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"N° {bail.numero_contrat} - {date.today().strftime('%d/%m/%Y')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 20))

    # Coordonnées du bailleur
    elements.append(Paragraph("<b>BAILLEUR</b>", bold_style))
    elements.append(Paragraph(
        f"{proprietaire.get_full_name()}<br/>"
        f"{proprietaire.adresse}<br/>"
        f"{proprietaire.code_postal} {proprietaire.ville}<br/>"
        f"Email : {proprietaire.email or 'Non renseigné'}<br/>"
        f"Tél : {proprietaire.telephone or 'Non renseigné'}",
        normal_style
    ))
    elements.append(Spacer(1, 15))

    # Coordonnées du locataire
    elements.append(Paragraph("<b>LOCATAIRE</b>", bold_style))
    elements.append(Paragraph(
        f"{locataire.get_full_name()}<br/>"
        f"{locataire.adresse}<br/>"
        f"{locataire.code_postal} {locataire.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 15))

    # Adresse du logement
    elements.append(Paragraph("<b>LOGEMENT CONCERNÉ</b>", bold_style))
    elements.append(Paragraph(
        f"{bien.get_type_bien_display()} - {bien.titre}<br/>"
        f"{bien.adresse}<br/>"
        f"{bien.code_postal} {bien.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 20))

    # Tableau de détail
    total_mensuel = bail.loyer_mensuel + bail.charges_mensuelles
    table_style_normal = ParagraphStyle('TableCellNormal', parent=normal_style, fontSize=10, alignment=TA_CENTER)
    table_style_bold = ParagraphStyle('TableCellBold', parent=normal_style, fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')
    table_style_header = ParagraphStyle('TableCellHeader', parent=normal_style, fontSize=11, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.white)
    
    data = [
        [Paragraph('Désignation', table_style_header), Paragraph('Montant', table_style_header)],
        [Paragraph('Loyer mensuel', table_style_normal), Paragraph(f"{bail.loyer_mensuel:.2f} €", table_style_normal)],
        [Paragraph('Charges mensuelles', table_style_normal), Paragraph(f"{bail.charges_mensuelles:.2f} €", table_style_normal)],
        [Paragraph('', table_style_normal), Paragraph('', table_style_normal)],
        [Paragraph(f'<b>Total à payer</b>', table_style_bold), Paragraph(f'<b>{total_mensuel:.2f} €</b>', table_style_bold)],
    ]
    
    table = Table(data, colWidths=[12*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (1, -2), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2c3e50')),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Informations de paiement
    elements.append(Paragraph("<b>INFORMATIONS DE PAIEMENT</b>", bold_style))
    elements.append(Paragraph(
        f"<b>Date limite :</b> le {bail.jour_paiement} du mois<br/>"
        f"<b>Modalité :</b> {bail.get_modalite_paiement_display()}<br/>"
        f"<b>IBAN :</b> {locataire.iban or 'Non renseigné'}",
        normal_style
    ))
    elements.append(Spacer(1, 20))

    # Mention légale
    elements.append(Paragraph(
        "<i>Ce document constitue un appel de loyer. "
        "Merci d'effectuer le paiement avant la date limite indiquée.</i>",
        ParagraphStyle('LegalStyle', parent=normal_style, fontSize=8,
                       textColor=colors.HexColor('#95a5a6'))
    ))
    elements.append(Spacer(1, 20))

    # Signature
    elements.append(Paragraph(
        f"Fait à {proprietaire.ville}, le {date.today().strftime('%d/%m/%Y')}",
        right_style
    ))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Signature du bailleur",
        right_style
    ))

    # Génération
    doc.build(elements)

    # Chemin relatif pour le stockage Django
    relative_path = f'appels_loyers/{os.path.basename(filepath)}'
    
    # Créer ou mettre à jour l'entrée Document
    from .models import Document as DocModel
    doc_obj, created = DocModel.objects.get_or_create(
        bien=bien,
        locataire=locataire,
        bail=bail,
        categorie='AUTR',
        titre=f"Appel de loyer - {mois_fr[mois]} {annee}",
        defaults={
            'fichier': relative_path,
            'notes': f"Appel de loyer généré le {date.today().strftime('%d/%m/%Y')} pour la période {mois:02d}/{annee}",
        }
    )
    if not created:
        doc_obj.fichier = relative_path
        doc_obj.save(update_fields=['fichier'])
    
    # Créer un paiement en attente associé à ce mois
    from .models import Paiement as PaiementModel
    import calendar
    
    # Calculer la fin de mois
    dernier_jour = calendar.monthrange(annee, mois)[1]
    date_debut_periode = date(annee, mois, 1)
    date_fin_periode = date(annee, mois, dernier_jour)
    total_mensuel = (bail.loyer_mensuel or 0) + (bail.charges_mensuelles or 0)
    
    # Vérifier si un paiement en attente existe déjà pour cette période
    paiement_existant = PaiementModel.objects.filter(
        bail=bail,
        locataire=locataire,
        date_periode_debut=date_debut_periode,
        date_periode_fin=date_fin_periode,
    ).first()
    
    if not paiement_existant:
        PaiementModel.objects.create(
            bail=bail,
            locataire=locataire,
            montant=bail.loyer_mensuel or 0,
            montant_charges=bail.charges_mensuelles or 0,
            date_paiement=date.today(),
            date_periode_debut=date_debut_periode,
            date_periode_fin=date_fin_periode,
            statut='EN_ATTENTE',
            mode_paiement=bail.modalite_paiement or 'VIR',
            notes=f"Appel de loyer généré le {date.today().strftime('%d/%m/%Y')}",
        )
    
    return filepath


def get_dashboard_stats():
    """Retourne les statistiques pour le dashboard."""
    from django.db.models import Sum, Count, Q
    from .models import BienImmobilier, Bail, Paiement, Locataire, Proprietaire, Intervention

    total_biens = BienImmobilier.objects.filter(actif=True).count()
    biens_loues = BienImmobilier.objects.filter(statut='LOUE', actif=True).count()
    biens_disponibles = BienImmobilier.objects.filter(statut='DISP', actif=True).count()
    
    total_proprietaires = Proprietaire.objects.filter(actif=True).count()
    total_locataires = Locataire.objects.filter(actif=True).count()
    
    baux_actifs = Bail.objects.filter(actif=True, resiliation=False).count()
    baux_expirant = Bail.objects.filter(
        actif=True, resiliation=False,
        date_fin__gte=date.today(),
        date_fin__lte=date.today() + timezone.timedelta(days=90)
    ).count()
    
    # Paiements
    paiements_mois = Paiement.objects.filter(
        date_paiement__month=date.today().month,
        date_paiement__year=date.today().year,
        statut='VALID'
    ).aggregate(
        total=Sum('montant'),
        count=Count('id')
    )
    
    # Impayés
    total_impayes = Paiement.objects.filter(statut='EN_RETARD').count()
    montant_impayes = Paiement.objects.filter(
        Q(statut='EN_RETARD') |
        Q(statut='EN_ATTENTE', date_paiement__lt=date.today())
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    # Interventions
    interventions_urgentes = Intervention.objects.filter(priorite='URG', statut__in=['AFAI', 'ENCO']).count()
    interventions_en_cours = Intervention.objects.filter(statut='ENCO').count()
    
    # Taux d'occupation
    taux_occupation = 0
    if total_biens > 0:
        taux_occupation = round((biens_loues / total_biens) * 100, 1)
    
    # Revenus annuels
    revenus_annuels = Paiement.objects.filter(
        date_paiement__year=date.today().year,
        statut='VALID'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    return {
        'total_biens': total_biens,
        'biens_loues': biens_loues,
        'biens_disponibles': biens_disponibles,
        'taux_occupation': taux_occupation,
        'total_proprietaires': total_proprietaires,
        'total_locataires': total_locataires,
        'baux_actifs': baux_actifs,
        'baux_expirant': baux_expirant,
        'paiements_mois': paiements_mois['total'] or 0,
        'paiements_mois_count': paiements_mois['count'] or 0,
        'total_impayes': total_impayes,
        'montant_impayes': montant_impayes,
        'interventions_urgentes': interventions_urgentes,
        'interventions_en_cours': interventions_en_cours,
        'revenus_annuels': revenus_annuels,
    }


def generate_graphiques():
    """Génère les graphiques pour le dashboard via matplotlib."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from io import BytesIO
    import base64
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    from .models import Paiement, BienImmobilier
    
    # Configuration matplotlib en français
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    
    graphs = {}
    
    # 1. Graphique des revenus mensuels (12 derniers mois)
    from datetime import date, timedelta
    twelve_months_ago = date.today() - timedelta(days=365)
    
    revenus_mensuels = Paiement.objects.filter(
        date_paiement__gte=twelve_months_ago,
        statut='VALID'
    ).annotate(
        mois=TruncMonth('date_paiement')
    ).values('mois').annotate(
        total=Sum('montant')
    ).order_by('mois')
    
    if revenus_mensuels:
        fig, ax = plt.subplots(figsize=(8, 4))
        mois = [str(r['mois'].strftime('%b %Y')) for r in revenus_mensuels]
        montants = [float(r['total']) for r in revenus_mensuels]
        
        ax.bar(mois, montants, color='#3498db', edgecolor='#2980b9')
        ax.set_title('Revenus mensuels (12 mois)')
        ax.set_ylabel('Montant (€)')
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        graphs['revenus_mensuels'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
    
    # 2. Répartition des biens par type
    types_biens = BienImmobilier.objects.filter(actif=True).values('type_bien').annotate(
        count=Count('id')
    )
    
    if types_biens:
        fig, ax = plt.subplots(figsize=(6, 6))
        labels = [str(dict(BienImmobilier._meta.get_field('type_bien').flatchoices).get(t['type_bien'], t['type_bien']))
                  for t in types_biens]
        values = [int(t['count']) for t in types_biens]
        colors_list = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors_list[:len(labels)],
               startangle=90, shadow=True)
        ax.set_title('Répartition par type de bien')
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        graphs['repartition_biens'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
    
    # 3. Statut des biens
    statuts = BienImmobilier.objects.filter(actif=True).values('statut').annotate(
        count=Count('id')
    )
    
    if statuts:
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = [str(dict(BienImmobilier._meta.get_field('statut').flatchoices).get(s['statut'], s['statut']))
                  for s in statuts]
        values = [int(s['count']) for s in statuts]
        colors_status = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#95a5a6']
        
        bars = ax.bar(labels, values, color=colors_status[:len(labels)])
        ax.set_title('Statut des biens')
        ax.set_ylabel('Nombre de biens')
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(val), ha='center', va='bottom')
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        graphs['statut_biens'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
    
    return graphs
