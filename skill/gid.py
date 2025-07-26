import logging
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from io import BytesIO
from reportlab.lib.pagesizes import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import qrcode
from io import BytesIO as IO
from datetime import datetime, timedelta
from django.utils.crypto import get_random_string
from reportlab.lib.utils import ImageReader
import os

logger = logging.getLogger(__name__)

def truncate_with_ellipsis(text, max_length):
    """Helper function to truncate text with ellipsis if too long"""
    if text and len(text) > max_length:
        return text[:max_length-1] + "…"
    return text

def draw_photo_placeholder(canvas, x, y):
    """Draw placeholder when photo is missing"""
    canvas.saveState()
    # Rectangle
    canvas.setFillColor(colors.HexColor('#e3f2fd'))
    canvas.setStrokeColor(colors.HexColor('#1a237e'))
    canvas.setLineWidth(1)
    canvas.roundRect(x, y, 25*mm, 25*mm, 3*mm, fill=1, stroke=1)
    
    # Icon
    canvas.setFont("Helvetica", 16)
    canvas.setFillColor(colors.HexColor('#1a237e'))
    canvas.drawCentredString(x + 12.5*mm, y + 12.5*mm - 8, "👤")
    
    # Text
    canvas.setFont("Helvetica", 6)
    canvas.setFillColor(colors.HexColor('#424242'))
    canvas.drawCentredString(x + 12.5*mm, y + 5*mm, "NO PHOTO")
    canvas.restoreState()

@login_required
def generate_id_card(request):
    try:
        # Check if user is a service provider
        if not hasattr(request.user, 'service_provider'):
            return HttpResponse("You are not registered as a service provider", status=403)
        
        provider = request.user.service_provider
        
        # Validate required fields
        required_fields = ['full_name', 'service_provider_id', 'mobile_number', 'Preference1']
        for field in required_fields:
            if not getattr(provider, field, None):
                logger.error(f"Missing required field {field} for provider {provider.id}")
                return HttpResponse(
                    "Your profile information is incomplete. Please complete your profile first.",
                    status=400
                )

        # Configuration with defaults
        site_config = {
            'name': getattr(settings, 'SITE_NAME', 'SkillSetGo'),
            'url': getattr(settings, 'SITE_URL', 'https://skillsetgo.in').replace('https://', '').replace('http://', ''),
            'email': getattr(settings, 'SITE_SUPPORT_EMAIL', 'support@skillsetgo.in')
        }

        # Security elements
        verification_token = get_random_string(16)
        dates = {
            'issued': datetime.now().strftime('%d %b %Y'),
            'expires': (datetime.now() + timedelta(days=365)).strftime('%d %b %Y')
        }

        # Get preferences with proper handling of "other" options
        try:
            # Primary preference
            if provider.Preference1 == 'others' and provider.other_preference1:
                pref1 = provider.other_preference1
            else:
                pref1 = provider.get_Preference1_display()
            pref1 = truncate_with_ellipsis(pref1 or "Service", 15)

            # Secondary preference (if exists)
            pref2 = None
            if provider.Preference2:
                if provider.Preference2 == 'others' and provider.other_preference2:
                    pref2 = provider.other_preference2
                else:
                    pref2 = provider.get_Preference2_display()
                pref2 = truncate_with_ellipsis(pref2, 15)
        except Exception as e:
            logger.error(f"Error processing preferences: {str(e)}")
            pref1 = "Service"
            pref2 = None

        # Create PDF buffer
        buffer = BytesIO()
        card_width, card_height = 85.6 * mm, 54 * mm  # Standard ID card size
        
        try:
            p = canvas.Canvas(buffer, pagesize=(card_width * 2 + 10*mm, card_height + 10*mm))

            # ===== FRONT SIDE =====
            front_x, front_y = 5*mm, 5*mm
            
            # Card base
            p.setFillColor(colors.white)
            p.setStrokeColor(colors.HexColor('#e0e0e0'))
            p.setLineWidth(0.8)
            p.roundRect(front_x, front_y, card_width, card_height, 5*mm, fill=1, stroke=1)
            
            # Header
            p.setFillColor(colors.HexColor('#1a237e'))
            p.roundRect(front_x, front_y + card_height - 15*mm, card_width, 15*mm, 5*mm, stroke=0, fill=1)
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.white)
            p.drawCentredString(front_x + card_width/2, front_y + card_height - 10*mm, "SKILLSETGO SERVICE ID")
            
            # Profile Image (Right Side)
            photo_size = 25*mm
            photo_x = front_x + card_width - photo_size - 5*mm
            photo_y = front_y + card_height - photo_size - 10*mm
            
            if provider.profile_photo and os.path.exists(provider.profile_photo.path):
                try:
                    img = ImageReader(provider.profile_photo.path)
                    # Photo with border
                    p.setFillColor(colors.white)
                    p.setStrokeColor(colors.HexColor('#1a237e'))
                    p.setLineWidth(1)
                    p.roundRect(photo_x, photo_y, photo_size, photo_size, 3*mm, fill=1, stroke=1)
                    p.drawImage(img, 
                              photo_x + 1*mm, 
                              photo_y + 1*mm, 
                              width=photo_size - 2*mm, 
                              height=photo_size - 2*mm, 
                              preserveAspectRatio=True,
                              mask='auto')
                except Exception as e:
                    logger.error(f"Profile photo error: {str(e)}")
                    draw_photo_placeholder(p, photo_x, photo_y)
            else:
                draw_photo_placeholder(p, photo_x, photo_y)
            
            # Text Content (Left Side)
            content_x = front_x + 5*mm
            content_y = front_y + card_height - 28*mm
            
            # Name
            p.setFont("Helvetica-Bold", 14)
            p.setFillColor(colors.black)
            p.drawString(content_x, content_y, truncate_with_ellipsis(provider.full_name, 20))
            
            # Service ID
            p.setFont("Helvetica", 10)
            p.setFillColor(colors.HexColor('#424242'))
            p.drawString(content_x, content_y - 8*mm, f"ID: {provider.service_provider_id}")
            
            # Expertise
            p.setFont("Helvetica-Bold", 10)
            p.setFillColor(colors.HexColor('#1a237e'))
            p.drawString(content_x, content_y - 18*mm, "EXPERTISE:")
            
            p.setFont("Helvetica", 10)
            p.setFillColor(colors.black)
            p.drawString(content_x + 22*mm, content_y - 18*mm, f"• {pref1}")
            if pref2:
                p.drawString(content_x + 22*mm, content_y - 25*mm, f"• {pref2}")
            
            # Expiry date
            p.setFont("Helvetica-Bold", 10)
            p.setFillColor(colors.HexColor('#d32f2f'))
            p.drawString(content_x, content_y - 35*mm, f"EXP: {dates['expires']}")

            # ===== BACK SIDE =====
            back_x = front_x + card_width + 10*mm
            
            # Card base
            p.setFillColor(colors.HexColor('#f5f5f5'))
            p.setStrokeColor(colors.HexColor('#e0e0e0'))
            p.setLineWidth(0.8)
            p.roundRect(back_x, front_y, card_width, card_height, 5*mm, fill=1, stroke=1)
            
            # Verification title
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.HexColor('#1a237e'))
            p.drawCentredString(back_x + card_width/2, front_y + card_height - 15*mm, "VERIFICATION")
            
            # Verification details
            detail_x = back_x + 10*mm
            detail_y = front_y + card_height - 30*mm
            
            verification_details = [
                ("MOBILE:", f" {provider.mobile_number}"),
                ("ISSUED:", dates['issued']),
                ("EXPIRES:", dates['expires']),
                ("CONTACT:", site_config['email']),
                ("URL:", site_config['url'])
            ]
            
            p.setFont("Helvetica", 9)
            for i, (label, value) in enumerate(verification_details):
                # Label
                p.setFillColor(colors.HexColor('#1a237e'))
                p.drawString(detail_x, detail_y - (i * 6*mm), label)
                # Value
                p.setFillColor(colors.black)
                p.drawString(detail_x + 18*mm, detail_y - (i * 6*mm), value)
            
            # QR code
            qr_size = 25*mm
            qr_x = back_x + card_width - qr_size - 10*mm
            qr_y = front_y + 10*mm
            
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=3,
                    border=2,
                )
                qr.add_data(f"{site_config['url']}/verify/{verification_token}/")
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#1a237e", back_color="#f5f5f5")
                
                qr_buffer = IO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                p.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)
                
                # QR code label
                p.setFont("Helvetica", 6)
                p.setFillColor(colors.HexColor('#616161'))
                p.drawCentredString(qr_x + qr_size/2, qr_y - 3*mm, "SCAN TO VERIFY")
            except Exception as e:
                logger.error(f"QR code error: {str(e)}")

            # Footer
            p.setFont("Helvetica-Oblique", 7)
            p.setFillColor(colors.HexColor('#757575'))
            p.drawCentredString(back_x + card_width/2, front_y + 5*mm, "Official document - Do not duplicate")

            p.showPage()
            p.save()
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
            raise
            
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{site_config["name"]}_ID_{provider.service_provider_id}.pdf"'
        return response
        
    except Exception as e:
        logger.critical(f"ID generation failed: {str(e)}", exc_info=True)
        return HttpResponse(
            "We couldn't generate your ID card. Please contact support.",
            status=500
        )