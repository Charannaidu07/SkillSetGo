import os
import sys
import json
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SkillSetGo.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from skill.models import (
    CustomUser,
    ServiceProviderDetails,
    ServiceProviderBankDetails,
    Book_Appointment,
    Bargaining
)

def run_tests():
    print("=" * 70)
    print("STARTING COMPREHENSIVE SKILLSETGO SYSTEM & FEATURE TEST SUITE")
    print("=" * 70)

    client = Client()
    results = []

    def log_result(test_name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        results.append((test_name, passed, details))
        print(f"[{status}] {test_name}: {details}")

    # 1. Test Homepage & Public Pages
    print("\n--- 1. PUBLIC ROUTES & STATIC PAGES ---")
    resp = client.get('/')
    log_result("GET / (Homepage)", resp.status_code == 200, f"Status code: {resp.status_code}")
    
    resp = client.get('/service')
    log_result("GET /service (Services Page)", resp.status_code == 200, f"Status code: {resp.status_code}")

    # 2. Test User Setup
    print("\n--- 2. AUTHENTICATION & USER ROLES ---")
    # Setup Customer
    cust_user, _ = CustomUser.objects.get_or_create(
        username="autotest_customer",
        defaults={"email": "autotest_customer@example.com", "user_type": "user"}
    )
    cust_user.set_password("TestSecret123!")
    cust_user.save()

    # Setup Servicer
    serv_user, _ = CustomUser.objects.get_or_create(
        username="autotest_servicer",
        defaults={"email": "autotest_servicer@example.com", "user_type": "servicer"}
    )
    serv_user.set_password("TestSecret123!")
    serv_user.save()

    # Setup Servicer Details
    sp_details, _ = ServiceProviderDetails.objects.get_or_create(
        user=serv_user,
        defaults={
            "full_name": "Auto Test Specialist",
            "mobile_number": "9876501234",
            "whatsapp_number": "9876501234",
            "alternate_number": "9876501235",
            "address": "45 Tech Boulevard, Outer Ring Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560103",
            "aadhar_number": "999988887777",
            "Preference1": "plumbing",
            "Preference2": "electrical",
            "is_verified": True
        }
    )

    sp_bank, _ = ServiceProviderBankDetails.objects.get_or_create(
        service_provider=sp_details,
        defaults={
            "pan_number": "ZZZZZ9999Z",
            "bank_account_number": "987654321012",
            "bank_name": "State Bank of India",
            "ifsc_code": "SBIN0001234",
            "upi_id": "autotest@oksbi",
            "upi_mobile_number": "9876501234",
            "is_verified": True
        }
    )

    # Test Customer Login
    login_success = client.login(username="autotest_customer", password="TestSecret123!")
    log_result("Customer Login via test client", login_success, "Successfully authenticated as autotest_customer")

    resp = client.get('/profile')
    log_result("Customer GET /profile", resp.status_code == 200, f"Status code: {resp.status_code}")

    # 3. Test Booking Flow
    print("\n--- 3. APPOINTMENT BOOKING FLOW ---")
    resp = client.get('/book_appointment')
    log_result("GET /book_appointment", resp.status_code == 200, f"Status code: {resp.status_code}")

    future_time = (timezone.now() + timedelta(days=2)).strftime('%m/%d/%Y %I:%M %p')
    post_data = {
        'full_name': 'Auto Test Customer',
        'contact_number': '9876501234',
        'issue': 'plumbing',
        'description': 'Automated test plumbing leakage repair at bathroom sink',
        'expected_amount': '750.00',
        'address': 'Flat 101, Sunshine Heights, Koramangala',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'country': 'India',
        'pincode': '560034',
        'expected_time': future_time
    }
    resp = client.post('/book_appointment', data=post_data, follow=True)
    log_result("POST /book_appointment (Create)", resp.status_code == 200, f"Redirected to: {resp.redirect_chain}")

    # Retrieve the newly created appointment
    created_app = Book_Appointment.objects.filter(user=cust_user, description__contains="Automated test plumbing").order_by('-created_at').first()
    has_app = created_app is not None
    log_result("Appointment Saved to DB", has_app, f"Booking ID: {created_app.booking_id if has_app else 'N/A'}")

    # 4. Test Customer View Appointments & API Details
    print("\n--- 4. APPOINTMENT DETAILS & CALCULATION API ---")
    resp = client.get('/appointments/')
    log_result("Customer GET /appointments/", resp.status_code == 200, f"Status code: {resp.status_code}")

    resp = client.get(f'/api/appointments/{created_app.id}/')
    log_result("GET /api/appointments/<id>/", resp.status_code == 200, f"Status code: {resp.status_code}")
    app_json = json.loads(resp.content.decode())
    log_result("API Details JSON contains expected fields", 'expected_amount' in app_json and app_json['issue'] == 'plumbing', f"Amount: Rs. {app_json.get('expected_amount')}")

    # 5. Test Servicer Login & Bookmarking
    print("\n--- 5. SERVICER WORKFLOW & BOOKMARKING ---")
    client.logout()
    serv_login = client.login(username="autotest_servicer", password="TestSecret123!")
    log_result("Servicer Login via test client", serv_login, "Successfully authenticated as autotest_servicer")

    resp = client.get('/dashboard/')
    log_result("Servicer GET /dashboard/", resp.status_code == 200, f"Status code: {resp.status_code}")

    resp = client.get('/appointments/')
    log_result("Servicer GET /appointments/", resp.status_code == 200, f"Status code: {resp.status_code}")

    # Bookmark appointment
    resp = client.post(f'/api/appointments/{created_app.id}/bookmark/')
    log_result("POST /api/appointments/<id>/bookmark/ (Add)", resp.status_code == 200, f"Response: {resp.content.decode()}")

    resp = client.get('/bookmarked_appointments/')
    log_result("Servicer GET /bookmarked_appointments/", resp.status_code == 200, f"Status code: {resp.status_code}")

    # 6. Test Bargaining Flow
    print("\n--- 6. BARGAINING & NEGOTIATION WORKFLOW ---")
    # Servicer submits counter-offer (₹850)
    bargain_payload = {
        'appointment_id': created_app.id,
        'servicer_offer': 850.00,
        'message': 'Includes specialized sealing materials and 30-day guarantee.'
    }
    resp = client.post(
        '/api/bargain/',
        data=json.dumps(bargain_payload),
        content_type='application/json'
    )
    log_result("Servicer POST /api/bargain/ (Counter Offer)", resp.status_code == 200, f"Response: {resp.content.decode()}")
    bargain_res = json.loads(resp.content.decode())
    bargain_id = bargain_res.get('bargain_id')

    # Switch to Customer to accept the offer
    client.logout()
    client.login(username="autotest_customer", password="TestSecret123!")

    resp = client.post(f'/api/bargain/{bargain_id}/accept/')
    log_result("Customer POST /api/bargain/<id>/accept/", resp.status_code == 200, f"Response: {resp.content.decode()}")

    # Verify appointment updated
    created_app.refresh_from_db()
    log_result("Appointment Status updated to 'accepted'", created_app.status == 'accepted', f"Status: {created_app.status}, Final Price: Rs. {created_app.expected_amount}, OTP: {created_app.otp}")

    # 7. Test Payment Workflow (Razorpay Integration)
    print("\n--- 7. PAYMENT FLOW (RAZORPAY INITIATE & VERIFY) ---")
    resp = client.post(f'/api/appointments/{created_app.id}/payment/initiate/')
    log_result("Customer POST /api/appointments/<id>/payment/initiate/", resp.status_code == 200, f"Response: {resp.content.decode()}")
    pay_json = json.loads(resp.content.decode())
    order_id = pay_json.get('order_id')
    amount_paise = pay_json.get('amount')

    # Simulate payment verification
    pay_id = f"pay_test_{created_app.id}_{int(timezone.now().timestamp())}"
    if order_id and settings.RAZORPAY_KEY_SECRET and not settings.RAZORPAY_KEY_SECRET.startswith('YOUR_'):
        import hmac, hashlib
        msg = f"{order_id}|{pay_id}".encode('utf-8')
        sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode('utf-8'), msg, hashlib.sha256).hexdigest()
    else:
        sig = 'simulated_valid_test_signature'

    verify_payload = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': pay_id,
        'razorpay_signature': sig
    }
    resp = client.post(
        f'/api/appointments/{created_app.id}/payment/verify/',
        data=json.dumps(verify_payload),
        content_type='application/json'
    )
    log_result("Customer POST /api/appointments/<id>/payment/verify/", resp.status_code == 200, f"Response: {resp.content.decode()}")
    created_app.refresh_from_db()
    log_result("Appointment payment_status updated to 'paid'", created_app.payment_status == 'paid', f"Payment status: {created_app.payment_status}")

    # 8. Test Servicer My Work & Job Execution
    print("\n--- 8. SERVICER 'MY WORK' & OTP VERIFICATION ---")
    client.logout()
    client.login(username="autotest_servicer", password="TestSecret123!")

    resp = client.get('/my_work/')
    log_result("Servicer GET /my_work/", resp.status_code == 200, f"Status code: {resp.status_code}")

    # Servicer enters OTP to complete job
    otp_payload = {'otp': created_app.otp}
    resp = client.post(
        f'/api/appointments/{created_app.id}/verify-otp/',
        data=json.dumps(otp_payload),
        content_type='application/json'
    )
    log_result("Servicer POST /api/appointments/<id>/verify-otp/", resp.status_code == 200, f"Response: {resp.content.decode()}")
    created_app.refresh_from_db()
    log_result("Appointment status updated to 'completed'", created_app.status == 'completed' and created_app.otp_verified, f"Status: {created_app.status}, OTP Verified: {created_app.otp_verified}")

    # 9. Test Customer Rating
    print("\n--- 9. CUSTOMER RATING & SERVICER SCORE UPDATE ---")
    client.logout()
    client.login(username="autotest_customer", password="TestSecret123!")

    rate_payload = {'rating': 5}
    resp = client.post(
        f'/api/appointments/{created_app.id}/rate-servicer/',
        data=json.dumps(rate_payload),
        content_type='application/json'
    )
    log_result("Customer POST /api/appointments/<id>/rate-servicer/ (5 Stars)", resp.status_code == 200, f"Response: {resp.content.decode()}")
    created_app.refresh_from_db()
    sp_details.refresh_from_db()
    log_result("Rating saved and Servicer rating updated", created_app.rating == 5 and sp_details.rating > 0, f"Appointment rating: {created_app.rating}, Servicer average rating: {sp_details.rating}")

    # 10. Test Servicer Payout Withdrawal & Dashboard Financials
    print("\n--- 10. SERVICER PAYOUT WITHDRAWAL & DASHBOARD LEDGER ---")
    client.logout()
    client.login(username="autotest_servicer", password="TestSecret123!")

    resp = client.post(f'/api/appointments/{created_app.id}/payout/withdraw/')
    log_result("Servicer POST /api/appointments/<id>/payout/withdraw/", resp.status_code == 200, f"Response: {resp.content.decode()}")
    created_app.refresh_from_db()
    log_result("Payout status updated to 'paid'", created_app.payout_status == 'paid', f"Txn ID: {created_app.payout_transaction_id}")

    resp = client.get('/dashboard/')
    log_result("Servicer GET /dashboard/ with completed payout", resp.status_code == 200, f"Status code: {resp.status_code}")

    # 11. Test ID Card PDF Generation
    print("\n--- 11. SERVICE ID CARD PDF GENERATION ---")
    resp = client.get('/generate_id_card/')
    log_result("Servicer GET /generate_id_card/ (ReportLab PDF)", resp.status_code == 200 and resp['Content-Type'] == 'application/pdf', f"Content-Type: {resp.get('Content-Type')}, Size: {len(resp.content)} bytes")

    # 12. Test New Premium Pages
    print("\n--- 12. PREMIUM MARKETPLACE PAGES & TOOLS ---")
    client.logout()
    client.login(username="autotest_customer", password="TestSecret123!")

    for page_url, page_name in [
        ('/help/', 'Help Center'),
        ('/reviews/', 'Customer Reviews'),
        ('/about/', 'About Us'),
        ('/trust/', 'Trust & Safety Shield'),
        ('/estimator/', 'Instant Cost Estimator'),
        ('/rewards/', 'Plus Rewards & Referral'),
        ('/terms/', 'Terms of Service'),
        ('/privacy/', 'Privacy Policy'),
        (f'/invoice/{created_app.id}/', 'Tax Invoice & Receipt'),
    ]:
        resp = client.get(page_url)
        log_result(f"GET {page_url} ({page_name})", resp.status_code == 200, f"Status: {resp.status_code}")

    # 13. Test Interactive APIs (Support Ticket & Notifications)
    print("\n--- 13. INTERACTIVE APIS (SUPPORT & NOTIFICATIONS) ---")
    tkt_payload = {
        'name': 'Auto Tester',
        'email': 'autotest@example.com',
        'category': 'Payment & Refund',
        'urgency': 'Normal',
        'message': 'Testing support ticket creation flow.'
    }
    resp = client.post('/api/support/ticket/', data=json.dumps(tkt_payload), content_type='application/json')
    log_result("POST /api/support/ticket/ (Support Ticket)", resp.status_code == 200, f"Response: {resp.content.decode()}")

    resp = client.get('/api/notifications/')
    log_result("GET /api/notifications/ (Notifications Feed)", resp.status_code == 200 and 'notifications' in resp.json(), f"Response: {resp.content.decode()[:80]}...")

    # 14. Summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"Total Features/Endpoints Tested: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
