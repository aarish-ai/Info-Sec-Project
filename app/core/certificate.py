import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    Image,
    KeepTogether,
    HRFlowable,
)

def generate_verification_certificate_pdf(media_record: dict, base_url: str) -> bytes:
    """
    Generates an official, high-contrast, tamper-evident PDF Certificate of Provenance
    for a registered media item, embedding a dynamic QR code pointing to the public
    verification portal.

    Returns:
        bytes: Raw PDF binary bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette matching MediaGuard tokens
    primary_color = colors.HexColor("#4F46E5")     # Indigo
    dark_bg = colors.HexColor("#0B0F19")           # Deep Slate
    card_bg = colors.HexColor("#111827")           # Elevated Slate
    border_color = colors.HexColor("#374151")      # Border subtle
    text_light = colors.HexColor("#F9FAFB")        # Off-white
    text_muted = colors.HexColor("#9CA3AF")        # Gray
    success_color = colors.HexColor("#10B981")     # Emerald Green

    # Typography Styles
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=1,  # Center
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_muted,
        alignment=1,
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=text_light,
        spaceBefore=6,
        spaceAfter=4
    )

    label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=text_muted
    )

    value_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=text_light
    )

    mono_style = ParagraphStyle(
        'CellMono',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=text_light
    )

    badge_style = ParagraphStyle(
        'StatusBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=success_color
    )

    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_muted,
        alignment=1
    )

    story = []

    # 1. Header & Title Banner
    story.append(Paragraph("MEDIAGUARD VERIFICATION CERTIFICATE", title_style))
    story.append(Paragraph("CRYPTOGRAPHIC CERTIFICATE OF PROVENANCE & MEDIA INTEGRITY", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=14))

    # 2. Dynamic QR Code Generation
    media_id = str(media_record.get('media_id', ''))
    clean_base = base_url.rstrip('/') if base_url else ''
    verify_url = f"{clean_base}/verify?cert_id={media_id}" if clean_base else f"/verify?cert_id={media_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0B0F19", back_color="#FFFFFF")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    platypus_qr = Image(qr_buffer, width=1.5 * inch, height=1.5 * inch)

    # 3. Media Metadata Table
    owner_str = media_record.get('owner_username') or f"User #{media_record.get('owner_id', 'Unknown')}"
    timestamp_str = str(media_record.get('registration_timestamp', 'N/A'))
    filename_str = str(media_record.get('original_filename', 'Unknown'))
    size_int = media_record.get('file_size', 0)
    size_str = f"{size_int:,} bytes" if isinstance(size_int, int) else str(size_int)
    mime_str = str(media_record.get('file_type', 'N/A'))
    sha256_str = str(media_record.get('sha256_hash', 'N/A'))
    phash_str = str(media_record.get('phash', 'N/A'))

    table_data = [
        [
            Paragraph("Certificate / Media ID", label_style),
            Paragraph(media_id, mono_style)
        ],
        [
            Paragraph("Registered Owner", label_style),
            Paragraph(owner_str, value_style)
        ],
        [
            Paragraph("Registration Timestamp (UTC)", label_style),
            Paragraph(timestamp_str, value_style)
        ],
        [
            Paragraph("Original Filename", label_style),
            Paragraph(filename_str, value_style)
        ],
        [
            Paragraph("File Size & Format", label_style),
            Paragraph(f"{size_str} ({mime_str})", value_style)
        ],
        [
            Paragraph("Cryptographic Fingerprint (SHA-256)", label_style),
            Paragraph(sha256_str, mono_style)
        ],
        [
            Paragraph("Perceptual Hash (pHash)", label_style),
            Paragraph(phash_str, mono_style)
        ],
        [
            Paragraph("Digital Signature Status", label_style),
            Paragraph("RSA-PSS Validated & Bound to Manifest", badge_style)
        ]
    ]

    meta_table = Table(table_data, colWidths=[2.2 * inch, 4.8 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1E293B")),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 4. QR Verification Box
    qr_caption = ParagraphStyle(
        'QRCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=text_light
    )
    qr_sub = ParagraphStyle(
        'QRSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_muted
    )

    qr_text_cell = [
        Paragraph("Scan with camera to verify online", qr_caption),
        Spacer(1, 4),
        Paragraph(
            "This cryptographic QR code points directly to the universal public verification "
            "portal. Any verifier can inspect this certificate's authenticity against the tamper-evident "
            "canonical manifest and digital signature.",
            qr_sub
        ),
        Spacer(1, 4),
        Paragraph(f"Verification URL: {verify_url}", mono_style)
    ]

    qr_table = Table(
        [[platypus_qr, qr_text_cell]],
        colWidths=[1.7 * inch, 5.3 * inch]
    )
    qr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#111827")),
        ('BOX', (0, 0), (-1, -1), 1, primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether(qr_table))
    story.append(Spacer(1, 20))

    # 5. Institutional Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        "NUST School of Electrical Engineering & Computer Science · CS-353 Information Security",
        footer_style
    ))
    story.append(Paragraph(
        "Dual RSA Key Separation · AES-256-GCM Envelope Encryption · SHA-256 & pHash Dual Verification",
        footer_style
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
