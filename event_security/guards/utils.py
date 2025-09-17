from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import qrcode
import io
from django.conf import settings
import os

def generate_guard_id_card(guard_profile):
    """
    Generate a professional ID card PDF for a security guard.
    """
    card_width, card_height = 86*mm, 54*mm  # Standard CR80 ID card size
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(card_width, card_height))

    # Background color / border
    c.setFillColorRGB(0.0, 0.3, 0.6)  # Navy blue top bar
    c.rect(0, card_height-12*mm, card_width, 12*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(card_width/2, card_height-8*mm, "DESAS Security ID Card")

    # Add watermark
    c.setFont("Helvetica", 40)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.saveState()
    c.translate(card_width/2, card_height/2)
    c.rotate(45)
    c.drawCentredString(0, 0, "DESAS")
    c.restoreState()

    # Guard photo
    if guard_profile.photo:
        photo_path = os.path.join(settings.MEDIA_ROOT, str(guard_profile.photo))
        if os.path.exists(photo_path):
            c.drawImage(
                ImageReader(photo_path),
                5*mm, card_height-45*mm,
                width=25*mm, height=30*mm
            )

    # Guard details
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    details_x = 35*mm
    details_y = card_height - 20*mm
    line_height = 6*mm

    details = [
        ("Name", guard_profile.user.username),
        ("CNIC", guard_profile.cnic),
        ("Type", guard_profile.get_guard_type_display()),
        ("Age", str(guard_profile.age)),
        ("Experience", f"{guard_profile.experience} years"),
    ]

    for label, value in details:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(details_x, details_y, f"{label}:")
        c.setFont("Helvetica", 8)
        c.drawString(details_x+20*mm, details_y, value)
        details_y -= line_height

    # QR code (link to guard verification, optional)
    qr_data = f"GuardID:{guard_profile.id}|Name:{guard_profile.user.username}"
    qr_img = qrcode.make(qr_data)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    c.drawImage(ImageReader(qr_buffer), card_width-22*mm, 5*mm, 18*mm, 18*mm)

    # Footer: Issue/Expiry
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)
    c.drawString(5*mm, 5*mm, "Issue Date: __________")
    c.drawString(35*mm, 5*mm, "Expiry Date: __________")

    c.save()
    buffer.seek(0)
    return buffer
