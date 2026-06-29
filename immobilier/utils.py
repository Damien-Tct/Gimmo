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

    import calendar
    dernier_jour = calendar.monthrange(annee, mois)[1]
    date_debut_periode = date(annee, mois, 1)
    date_fin_periode = date(annee, mois, dernier_jour)

    elements = []

    # En-tête
    elements.append(Paragraph("AVIS D'ÉCHÉANCE", title_style))
    elements.append(Paragraph(
        f"Période du {date_debut_periode.strftime('%d/%m/%Y')} au {date_fin_periode.strftime('%d/%m/%Y')}",
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
            'notes': f"Appel de loyer généré le {date.today().strftime('%d/%m/%Y')} pour la période du {date_debut_periode.strftime('%d/%m/%Y')} au {date_fin_periode.strftime('%d/%m/%Y')}",
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


def generer_consentement_rgpd_pdf(bail):
    """
    Génère un document PDF de consentement RGPD pour un locataire :
    - Autorisation d'exploitation des données à caractère personnel
    - Droit au stockage informatique des documents
    Retourne le chemin du fichier PDF.
    """
    bien = bail.bien
    proprietaire = bien.proprietaire
    locataire = bail.locataire

    # Nom du fichier
    filename = f"consentement_rgpd_{bail.numero_contrat}_{locataire.id}.pdf"
    dir_path = os.path.join(settings.MEDIA_ROOT, 'consentements_rgpd')
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
        fontSize=16, spaceAfter=12, alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    subtitle_style = ParagraphStyle(
        'SubtitleCustom', parent=styles['Normal'],
        fontSize=11, spaceAfter=16, alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    section_style = ParagraphStyle(
        'SectionCustom', parent=styles['Normal'],
        fontSize=12, spaceAfter=8, spaceBefore=14,
        fontName='Helvetica-Bold', textColor=colors.HexColor('#2c3e50')
    )
    normal_style = ParagraphStyle(
        'NormalCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6, leading=14
    )
    bold_style = ParagraphStyle(
        'BoldCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    small_style = ParagraphStyle(
        'SmallCustom', parent=styles['Normal'],
        fontSize=8, spaceAfter=4,
        textColor=colors.HexColor('#95a5a6')
    )
    right_style = ParagraphStyle(
        'RightCustom', parent=styles['Normal'],
        fontSize=10, spaceAfter=6, alignment=TA_RIGHT
    )

    elements = []

    # ── En-tête ──
    elements.append(Paragraph(
        "CONSENTEMENT RELATIF À LA PROTECTION<br/>DES DONNÉES PERSONNELLES",
        title_style
    ))
    elements.append(Paragraph(
        f"Document établi le {date.today().strftime('%d/%m/%Y')} — Réf. {bail.numero_contrat}",
        subtitle_style
    ))
    elements.append(Spacer(1, 10))

    # ── Parties ──
    elements.append(Paragraph("PARTIES", section_style))
    elements.append(Paragraph(
        f"<b>Le Bailleur :</b> {proprietaire.get_full_name()}<br/>"
        f"{proprietaire.adresse}<br/>"
        f"{proprietaire.code_postal} {proprietaire.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"<b>Le Locataire :</b> {locataire.get_full_name()}<br/>"
        f"Né(e) le {locataire.date_naissance.strftime('%d/%m/%Y') if locataire.date_naissance else 'Non renseignée'}<br/>"
        f"{locataire.adresse}<br/>"
        f"{locataire.code_postal} {locataire.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 8))

    # ── Logement concerné ──
    elements.append(Paragraph("LOGEMENT CONCERNÉ", section_style))
    elements.append(Paragraph(
        f"{bien.get_type_bien_display()} — {bien.titre}<br/>"
        f"{bien.adresse}<br/>"
        f"{bien.code_postal} {bien.ville}",
        normal_style
    ))
    elements.append(Spacer(1, 12))

    # ── Objet du consentement ──
    elements.append(Paragraph("OBJET DU CONSENTEMENT", section_style))
    elements.append(Paragraph(
        "Conformément au Règlement Général sur la Protection des Données (RGPD — "
        "Règlement UE 2016/679) et à la loi Informatique et Libertés du 6 janvier 1978 "
        "modifiée, le présent document formalise le consentement du Locataire concernant "
        "le traitement de ses données à caractère personnel par le Bailleur dans le cadre "
        "de la gestion du contrat de location.",
        normal_style
    ))
    elements.append(Spacer(1, 10))

    # ── Article 1 : Données collectées ──
    elements.append(Paragraph("ARTICLE 1 — DONNÉES COLLECTÉES", section_style))
    elements.append(Paragraph(
        "Les données à caractère personnel collectées et traitées par le Bailleur sont "
        "strictement nécessaires à la gestion du contrat de location et comprennent :",
        normal_style
    ))
    donnees_liste = [
        "• Identité : civilité, nom, prénom, date de naissance ;",
        "• Coordonnées : adresse postale, adresse email, numéro(s) de téléphone ;",
        "• Situation professionnelle : profession, employeur ;",
        "• Données financières : IBAN, modalités de paiement, historique des paiements ;",
        "• Documents justificatifs : pièce d'identité, justificatif de domicile, "
        "justificatif de revenus ;",
        "• Documents contractuels : contrat de bail, état des lieux, quittances de loyer, "
        "avis d'échéance, diagnostics techniques ;",
        "• Données de contact des garants éventuels.",
    ]
    for ligne in donnees_liste:
        elements.append(Paragraph(ligne, normal_style))
    elements.append(Spacer(1, 10))

    # ── Article 2 : Finalités du traitement ──
    elements.append(Paragraph("ARTICLE 2 — FINALITÉS DU TRAITEMENT", section_style))
    elements.append(Paragraph(
        "Les données personnelles du Locataire sont collectées et traitées pour les "
        "finalités exclusives suivantes :",
        normal_style
    ))
    finalites = [
        "• Gestion du contrat de location (établissement, suivi, renouvellement, "
        "résiliation) ;",
        "• Gestion comptable et financière (facturation des loyers et charges, édition "
        "des quittances et avis d'échéance, suivi des paiements et relances) ;",
        "• Gestion des interventions et travaux dans le logement ;",
        "• Communication avec le Locataire (informations relatives au bail, travaux, "
        "visites, état des lieux) ;",
        "• Respect des obligations légales et réglementaires (obligations fiscales, "
        "lutte contre le blanchiment, contentieux éventuels) ;",
        "• Constitution et conservation du dossier locatif.",
    ]
    for ligne in finalites:
        elements.append(Paragraph(ligne, normal_style))
    elements.append(Spacer(1, 10))

    # ── Article 3 : Droit au stockage informatique ──
    elements.append(Paragraph(
        "ARTICLE 3 — DROIT AU STOCKAGE INFORMATIQUE", section_style
    ))
    elements.append(Paragraph(
        "Le Locataire reconnaît et accepte expressément que l'ensemble des documents "
        "relatifs au contrat de location (bail, états des lieux, quittances, avis "
        "d'échéance, factures, diagnostics, correspondances, justificatifs) fassent "
        "l'objet d'une conservation sous format numérique (stockage informatique) par "
        "le Bailleur.",
        normal_style
    ))
    elements.append(Paragraph(
        "Ce stockage informatique est réalisé sur des serveurs sécurisés situés au sein "
        "de l'Union Européenne. Les mesures techniques et organisationnelles appropriées "
        "sont mises en œuvre afin de garantir la sécurité, la confidentialité et "
        "l'intégrité des données stockées, conformément à l'article 32 du RGPD.",
        normal_style
    ))
    elements.append(Paragraph(
        "Les documents numérisés ont la même valeur probante que les originaux papier, "
        "conformément aux articles 1366 et suivants du Code civil relatifs à la signature "
        "et à l'archivage électroniques.",
        normal_style
    ))
    elements.append(Spacer(1, 10))

    # ── Article 4 : Durée de conservation ──
    elements.append(Paragraph("ARTICLE 4 — DURÉE DE CONSERVATION", section_style))
    elements.append(Paragraph(
        "Les données personnelles et documents sont conservés pendant toute la durée du "
        "contrat de location. À l'issue de celui-ci, elles sont conservées pour une "
        "durée de :",
        normal_style
    ))
    durees = [
        "• <b>5 ans</b> à compter de la fin du bail pour les documents comptables, "
        "quittances et avis d'échéance (article L.123-22 du Code de commerce) ;",
        "• <b>3 ans</b> à compter de la fin du bail pour les documents relatifs au "
        "contrat de location (prescription de l'action en paiement du loyer — article "
        "7-1 de la loi du 6 juillet 1989) ;",
        "• <b>10 ans</b> pour les états des lieux et documents relatifs au dépôt de "
        "garantie.",
    ]
    for ligne in durees:
        elements.append(Paragraph(ligne, normal_style))
    elements.append(Spacer(1, 10))

    # ── Article 5 : Droits du Locataire ──
    elements.append(Paragraph("ARTICLE 5 — DROITS DU LOCATAIRE", section_style))
    elements.append(Paragraph(
        "Conformément au RGPD, le Locataire dispose à tout moment des droits suivants "
        "sur ses données personnelles :",
        normal_style
    ))
    droits = [
        "• <b>Droit d'accès</b> (article 15) : obtenir la confirmation que des données "
        "sont traitées et en recevoir une copie ;",
        "• <b>Droit de rectification</b> (article 16) : faire corriger des données "
        "inexactes ou incomplètes ;",
        "• <b>Droit à l'effacement</b> (article 17) : demander la suppression des "
        "données dans les limites légales ;",
        "• <b>Droit à la limitation</b> (article 18) : restreindre temporairement le "
        "traitement ;",
        "• <b>Droit à la portabilité</b> (article 20) : récupérer les données dans un "
        "format structuré ;",
        "• <b>Droit d'opposition</b> (article 21) : s'opposer au traitement pour des "
        "motifs légitimes ;",
        "• <b>Droit de retirer son consentement</b> (article 7) à tout moment.",
    ]
    for ligne in droits:
        elements.append(Paragraph(ligne, normal_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Ces droits peuvent être exercés en contactant le Bailleur à l'adresse suivante :<br/>"
        f"{proprietaire.adresse}, {proprietaire.code_postal} {proprietaire.ville}<br/>"
        f"Email : {proprietaire.email or 'Non renseigné'}",
        normal_style
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "En cas de difficulté, le Locataire peut également introduire une réclamation "
        "auprès de la Commission Nationale de l'Informatique et des Libertés (CNIL) — "
        "www.cnil.fr — 3 Place de Fontenoy, 75007 Paris.",
        normal_style
    ))
    elements.append(Spacer(1, 10))

    # ── Article 6 : Consentement ──
    elements.append(Paragraph("ARTICLE 6 — CONSENTEMENT", section_style))
    elements.append(Paragraph(
        "Par la présente, le Locataire soussigné :",
        normal_style
    ))
    elements.append(Paragraph(
        "<b>1. Autorise</b> expressément le Bailleur à collecter, traiter et conserver "
        "les données à caractère personnel énumérées à l'Article 1 pour les finalités "
        "décrites à l'Article 2, conformément au RGPD et à la loi Informatique et "
        "Libertés modifiée.",
        normal_style
    ))
    elements.append(Paragraph(
        "<b>2. Accepte</b> le stockage sous format informatique de l'ensemble des "
        "documents relatifs au contrat de location (bail, quittances, avis d'échéance, "
        "états des lieux, diagnostics, correspondances, justificatifs) dans les "
        "conditions prévues à l'Article 3.",
        normal_style
    ))
    elements.append(Paragraph(
        "<b>3. Reconnaît</b> avoir été informé(e) de ses droits tels que détaillés à "
        "l'Article 5 et des modalités de leur exercice.",
        normal_style
    ))
    elements.append(Spacer(1, 16))

    # ── Bloc signatures ──
    table_style_header = ParagraphStyle(
        'TableCellHeader', parent=normal_style,
        fontSize=10, alignment=TA_CENTER,
        fontName='Helvetica-Bold', textColor=colors.white
    )
    table_style_cell = ParagraphStyle(
        'TableCellCell', parent=normal_style,
        fontSize=10, alignment=TA_LEFT
    )

    data = [
        [
            Paragraph(
                f"<b>LE BAILLEUR</b><br/><br/>"
                f"{proprietaire.get_full_name()}<br/>"
                f"Fait à {proprietaire.ville}<br/>"
                f"Le {date.today().strftime('%d/%m/%Y')}<br/><br/>"
                f"<i>Signature :</i><br/><br/><br/><br/><br/>",
                table_style_cell
            ),
            Paragraph(
                f"<b>LE LOCATAIRE</b><br/><br/>"
                f"{locataire.get_full_name()}<br/>"
                f"Fait à {locataire.ville}<br/>"
                f"Le __/__/____<br/><br/>"
                f"<i>Signature précédée de la mention<br/>"
                f"« Lu et approuvé — Bon pour consentement » :</i><br/><br/><br/>",
                table_style_cell
            ),
        ]
    ]

    table = Table(data, colWidths=[8*cm, 8*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('LINEBETWEEN', (0, 0), (-1, -1), 1, colors.HexColor('#95a5a6')),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # ── Mention légale ──
    elements.append(Paragraph(
        "<i>Le présent consentement est établi en double exemplaire. Un exemplaire "
        "est remis au Locataire, l'autre est conservé par le Bailleur. Le Locataire "
        "peut retirer son consentement à tout moment par courrier recommandé avec "
        "accusé de réception. Ce retrait ne porte pas atteinte à la licéité du "
        "traitement fondé sur le consentement effectué avant ce retrait. Le retrait "
        "du consentement ne fait pas obstacle à la conservation des données "
        "nécessaires au respect d'une obligation légale à laquelle le Bailleur est "
        "soumis.</i>",
        small_style
    ))

    # Génération
    doc.build(elements)

    # Sauvegarde dans le modèle Document
    from .models import Document as DocModel
    relative_path = f'consentements_rgpd/{filename}'

    doc_obj, created = DocModel.objects.get_or_create(
        bien=bien,
        locataire=locataire,
        bail=bail,
        categorie='AUTR',
        titre=f"Consentement RGPD — {locataire.get_full_name()}",
        defaults={
            'fichier': relative_path,
            'notes': f"Consentement RGPD généré le {date.today().strftime('%d/%m/%Y')} "
                     f"— Bail {bail.numero_contrat}",
        }
    )
    if not created:
        doc_obj.fichier = relative_path
        doc_obj.notes = (
            f"Consentement RGPD régénéré le {date.today().strftime('%d/%m/%Y')} "
            f"— Bail {bail.numero_contrat}"
        )
        doc_obj.save(update_fields=['fichier', 'notes'])

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
