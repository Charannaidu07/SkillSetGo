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

def draw_photo_placeholder(canvas, x, y, size):
    """Draw placeholder when photo is missing"""
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#f1f5f9'))
    canvas.setStrokeColor(colors.HexColor('#94a3b8'))
    canvas.setLineWidth(1)
    canvas.roundRect(x, y, size, size, 3*mm, fill=1, stroke=1)
    
    canvas.setFont("Helvetica-Bold", 18)
    canvas.setFillColor(colors.HexColor('#0f172a'))
    canvas.drawCentredString(x + size/2, y + size/2 - 3*mm, "PRO")
    
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.drawCentredString(x + size/2, y + 4*mm, "VERIFIED AGENT")
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
            'url': getattr(settings, 'SITE_URL', 'https://skillsetgo.com').replace('https://', '').replace('http://', ''),
            'email': getattr(settings, 'SITE_SUPPORT_EMAIL', 'support@skillsetgo.com')
        }

        # Security elements
        dates = {
            'issued': datetime.now().strftime('%d %b %Y'),
            'expires': (datetime.now() + timedelta(days=365)).strftime('%d %b %Y')
        }

        # Get preferences with proper handling of "other" options
        try:
            if provider.Preference1 == 'others' and provider.other_preference1:
                pref1 = provider.other_preference1
            else:
                pref1 = provider.get_Preference1_display()
            pref1 = truncate_with_ellipsis(pref1 or "General Service", 18)

            pref2 = None
            if provider.Preference2:
                if provider.Preference2 == 'others' and provider.other_preference2:
                    pref2 = provider.other_preference2
                else:
                    pref2 = provider.get_Preference2_display()
                pref2 = truncate_with_ellipsis(pref2, 18)
        except Exception as e:
            logger.error(f"Error processing preferences: {str(e)}")
            pref1 = "General Service"
            pref2 = None

        # Create PDF buffer
        buffer = BytesIO()
        card_width, card_height = 92 * mm, 58 * mm  # Modern High-Definition ID card size
        
        try:
            p = canvas.Canvas(buffer, pagesize=(card_width * 2 + 15*mm, card_height + 15*mm))

            # ==============================================================
            # ===== FRONT SIDE =============================================
            # ==============================================================
            front_x, front_y = 6*mm, 7*mm
            
            # Card base background (Clean crisp card with subtle border)
            p.setFillColor(colors.HexColor('#ffffff'))
            p.setStrokeColor(colors.HexColor('#cbd5e1'))
            p.setLineWidth(1)
            p.roundRect(front_x, front_y, card_width, card_height, 4*mm, fill=1, stroke=1)
            
            # Header Bar: Deep Slate / Navy `#0f172a`
            header_h = 16*mm
            p.setFillColor(colors.HexColor('#0f172a'))
            p.roundRect(front_x, front_y + card_height - header_h, card_width, header_h, 4*mm, stroke=0, fill=1)
            # Cover lower rounded corners of header bar so it seamlessly merges with card
            p.rect(front_x, front_y + card_height - header_h, card_width, 4*mm, stroke=0, fill=1)
            
            # Draw SkillSetGo Logo on Top-Left of Header
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo.png')
            if os.path.exists(logo_path):
                try:
                    # White pill container for ultra-crisp logo presentation
                    p.setFillColor(colors.HexColor('#ffffff'))
                    p.roundRect(front_x + 3*mm, front_y + card_height - header_h + 2.5*mm, 34*mm, 11*mm, 2.5*mm, stroke=0, fill=1)
                    logo_img = ImageReader(logo_path)
                    p.drawImage(logo_img, front_x + 4*mm, front_y + card_height - header_h + 3.2*mm, width=32*mm, height=9.6*mm, preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    logger.error(f"Error drawing logo on ID card: {e}")
                    p.setFont("Helvetica-Bold", 12)
                    p.setFillColor(colors.white)
                    p.drawString(front_x + 4*mm, front_y + card_height - 11*mm, "SkillSetGo PRO")
            else:
                p.setFont("Helvetica-Bold", 12)
                p.setFillColor(colors.white)
                p.drawString(front_x + 4*mm, front_y + card_height - 11*mm, "SkillSetGo PRO")

            # Top-Right Header Badge: "VERIFIED PRO" in Emerald
            p.setFillColor(colors.HexColor('#10b981'))
            badge_w, badge_h = 28*mm, 7*mm
            p.roundRect(front_x + card_width - badge_w - 3*mm, front_y + card_height - header_h + 4.5*mm, badge_w, badge_h, 2*mm, stroke=0, fill=1)
            p.setFont("Helvetica-Bold", 7.5)
            p.setFillColor(colors.white)
            p.drawCentredString(front_x + card_width - badge_w/2 - 3*mm, front_y + card_height - header_h + 6.8*mm, "✓ VERIFIED PRO")

            # Profile Photo (Right Side)
            photo_size = 28*mm
            photo_x = front_x + card_width - photo_size - 4*mm
            photo_y = front_y + card_height - header_h - photo_size - 2*mm
            
            if provider.profile_photo and os.path.exists(provider.profile_photo.path):
                try:
                    img = ImageReader(provider.profile_photo.path)
                    p.setFillColor(colors.white)
                    p.setStrokeColor(colors.HexColor('#0f172a'))
                    p.setLineWidth(1.5)
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
                    draw_photo_placeholder(p, photo_x, photo_y, photo_size)
            else:
                draw_photo_placeholder(p, photo_x, photo_y, photo_size)

            # Left Text Content
            content_x = front_x + 4.5*mm
            
            # Servicer Full Name
            name_y = front_y + card_height - header_h - 6*mm
            p.setFont("Helvetica-Bold", 12.5)
            p.setFillColor(colors.HexColor('#0f172a'))
            p.drawString(content_x, name_y, truncate_with_ellipsis(provider.full_name, 19))

            # --- PROMINENT & BIGGER SERVICER ID BADGE ---
            badge_id_y = name_y - 8.5*mm
            badge_id_w = 48*mm
            badge_id_h = 7.5*mm
            
            # High-impact navy badge container with cyan border
            p.setFillColor(colors.HexColor('#0f172a'))
            p.setStrokeColor(colors.HexColor('#0284c7'))
            p.setLineWidth(1.2)
            p.roundRect(content_x, badge_id_y, badge_id_w, badge_id_h, 2*mm, fill=1, stroke=1)
            
            # Monospace-style Bold Servicer ID text
            p.setFont("Helvetica-Bold", 9.5)
            p.setFillColor(colors.HexColor('#38bdf8'))
            p.drawString(content_x + 2.5*mm, badge_id_y + 2.2*mm, "PRO ID:")
            
            p.setFont("Helvetica-Bold", 10)
            p.setFillColor(colors.white)
            p.drawString(content_x + 17*mm, badge_id_y + 2.2*mm, f"{provider.service_provider_id}")

            # Expertise / Trade Specialty
            skills_y = badge_id_y - 6*mm
            p.setFont("Helvetica-Bold", 7.5)
            p.setFillColor(colors.HexColor('#64748b'))
            p.drawString(content_x, skills_y, "PRIMARY SKILL:")
            
            p.setFont("Helvetica-Bold", 8.5)
            p.setFillColor(colors.HexColor('#0f172a'))
            p.drawString(content_x + 23*mm, skills_y, f"{pref1}")

            if pref2:
                p.setFont("Helvetica-Bold", 8)
                p.setFillColor(colors.HexColor('#475569'))
                p.drawString(content_x + 23*mm, skills_y - 4*mm, f"& {pref2}")

            # Validity / Expiry Date Badge
            exp_y = front_y + 3.5*mm
            p.setFont("Helvetica-Bold", 7)
            p.setFillColor(colors.HexColor('#059669'))
            p.drawString(content_x, exp_y, f"VALID THRU: {dates['expires']}")

            # Decorative Security Micro-Bar along bottom edge
            bar_w = card_width / 3
            p.setFillColor(colors.HexColor('#0284c7'))
            p.rect(front_x, front_y, bar_w, 1.2*mm, stroke=0, fill=1)
            p.setFillColor(colors.HexColor('#10b981'))
            p.rect(front_x + bar_w, front_y, bar_w, 1.2*mm, stroke=0, fill=1)
            p.setFillColor(colors.HexColor('#6366f1'))
            p.rect(front_x + bar_w*2, front_y, bar_w, 1.2*mm, stroke=0, fill=1)

            # ==============================================================
            # ===== BACK SIDE ==============================================
            # ==============================================================
            back_x = front_x + card_width + 8*mm
            
            # Card base
            p.setFillColor(colors.HexColor('#f8fafc'))
            p.setStrokeColor(colors.HexColor('#cbd5e1'))
            p.setLineWidth(1)
            p.roundRect(back_x, front_y, card_width, card_height, 4*mm, fill=1, stroke=1)
            
            # Header Bar
            p.setFillColor(colors.HexColor('#0f172a'))
            p.roundRect(back_x, front_y + card_height - header_h, card_width, header_h, 4*mm, stroke=0, fill=1)
            p.rect(back_x, front_y + card_height - header_h, card_width, 4*mm, stroke=0, fill=1)
            
            p.setFont("Helvetica-Bold", 10)
            p.setFillColor(colors.white)
            p.drawCentredString(back_x + card_width/2, front_y + card_height - 9.5*mm, "OFFICIAL VERIFICATION & CREDENTIALS")
            
            # Verification Details
            detail_x = back_x + 4.5*mm
            detail_y = front_y + card_height - header_h - 6*mm
            
            verification_details = [
                ("SERVICER ID:", f"{provider.service_provider_id}"),
                ("MOBILE NO:", f"+91 {provider.mobile_number}"),
                ("ISSUED ON:", dates['issued']),
                ("VALID THRU:", dates['expires']),
                ("SUPPORT:", site_config['email']),
                ("OFFICIAL URL:", site_config['url'])
            ]
            
            p.setFont("Helvetica", 7.5)
            for i, (label, value) in enumerate(verification_details):
                cur_y = detail_y - (i * 4.8*mm)
                # Label
                p.setFont("Helvetica-Bold", 7.5)
                p.setFillColor(colors.HexColor('#475569'))
                p.drawString(detail_x, cur_y, label)
                # Value
                if label == "SERVICER ID:":
                    p.setFont("Helvetica-Bold", 8)
                    p.setFillColor(colors.HexColor('#0284c7'))
                else:
                    p.setFont("Helvetica-Bold", 7.5)
                    p.setFillColor(colors.HexColor('#0f172a'))
                p.drawString(detail_x + 23*mm, cur_y, value)
            
            # QR Code for Live Verification
            qr_size = 23*mm
            qr_x = back_x + card_width - qr_size - 4.5*mm
            qr_y = front_y + 8*mm
            
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=3,
                    border=2,
                )
                qr.add_data(f"https://{site_config['url']}/verify/{provider.service_provider_id}/")
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
                
                qr_buffer = IO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                p.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)
                
                # QR label
                p.setFont("Helvetica-Bold", 5.5)
                p.setFillColor(colors.HexColor('#0f172a'))
                p.drawCentredString(qr_x + qr_size/2, qr_y - 2.8*mm, "SCAN TO VERIFY BADGE")
            except Exception as e:
                logger.error(f"QR code error: {str(e)}")

            # Footer Security Disclaimer
            p.setFont("Helvetica", 6)
            p.setFillColor(colors.HexColor('#94a3b8'))
            p.drawCentredString(back_x + card_width/2, front_y + 2.5*mm, "Property of SkillSetGo Marketplace. If found, please return to support@skillsetgo.com")

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