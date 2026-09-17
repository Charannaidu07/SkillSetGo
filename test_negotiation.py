import os
import sys
import json
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SkillSetGo.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from skill.models import (
    CustomUser,
    ServiceProviderDetails,
    ServiceProviderBankDetails,
    Book_Appointment,
    Bargaining
)

def test_price_negotiation():
    print("=" * 70)
    print("STARTING DEDICATED PRICE NEGOTIATION TEST SUITE")
    print("=" * 70)

    client = Client()
    results = []

    def log_result(test_name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        results.append((test_name, passed, details))
        print(f"[{status}] {test_name}: {details}")

    # Setup Customer
    cust, _ = CustomUser.objects.get_or_create(
        username="neg_customer",
        defaults={"email": "neg_customer@example.com", "user_type": "user"}
    )
    cust.set_password("NegSecret123!")
    cust.save()

    # Setup Servicer
    serv, _ = CustomUser.objects.get_or_create(
        username="neg_servicer",
        defaults={"email": "neg_servicer@example.com", "user_type": "servicer"}
    )
    serv.set_password("NegSecret123!")
    serv.save()

    sp, _ = ServiceProviderDetails.objects.get_or_create(
        user=serv,
        defaults={
            "full_name": "Negotiation Master Technician",
            "mobile_number": "9811223344",
            "whatsapp_number": "9811223344",
            "alternate_number": "9811223345",
            "address": "77 Market Rd",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
            "aadhar_number": "888877776666",
            "Preference1": "plumbing",
            "is_verified": True
        }
    )

    # 1. Customer creates appointment with budget ₹500
    print("\n--- 1. CUSTOMER APPOINTMENT CREATION ---")
    client.login(username="neg_customer", password="NegSecret123!")
    future_time = (timezone.now() + timedelta(days=2)).strftime('%m/%d/%Y %I:%M %p')
    post_data = {
        'full_name': 'Negotiation Customer',
        'contact_number': '9811223344',
        'issue': 'plumbing',
        'description': 'Pipe joint leaking under kitchen counter',
        'expected_amount': '500.00',
        'address': '10 Park Avenue',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'country': 'India',
        'pincode': '560001',
        'expected_time': future_time
    }
    client.post('/book_appointment', data=post_data)
    app = Book_Appointment.objects.filter(user=cust, description__contains="Pipe joint leaking").order_by('-created_at').first()
    log_result("Appointment Created (Budget Rs. 500)", app is not None and float(app.expected_amount) == 500.0, f"App ID: {app.id}")

    # 2. Servicer Submits First Counter-Offer (₹700)
    print("\n--- 2. SERVICER COUNTER-OFFER (Rs. 700) ---")
    client.logout()
    client.login(username="neg_servicer", password="NegSecret123!")

    offer_1 = {
        'appointment_id': app.id,
        'servicer_offer': 700.00,
        'message': 'Includes standard sealing parts.'
    }
    resp = client.post('/api/bargain/', data=json.dumps(offer_1), content_type='application/json')
    log_result("Servicer Submits Offer Rs. 700", resp.status_code == 200, f"Response: {resp.content.decode()}")

    # 3. Servicer Updates Counter-Offer (₹650)
    print("\n--- 3. SERVICER UPDATES OFFER TO Rs. 650 ---")
    offer_2 = {
        'appointment_id': app.id,
        'servicer_offer': 650.00,
        'message': 'Discounted quote: Rs. 650 with quick arrival.'
    }
    resp = client.post('/api/bargain/', data=json.dumps(offer_2), content_type='application/json')
    log_result("Servicer Updates Offer to Rs. 650", resp.status_code == 200, f"Response: {resp.content.decode()}")

    # 4. Customer Checks Appointment Details API
    print("\n--- 4. CUSTOMER RETRIEVES BARGAIN HISTORY ---")
    client.logout()
    client.login(username="neg_customer", password="NegSecret123!")

    resp = client.get(f'/api/appointments/{app.id}/')
    log_result("Customer GET /api/appointments/<id>/", resp.status_code == 200, f"Status: {resp.status_code}")
    details = json.loads(resp.content.decode())
    b_history = details.get('bargaining_history', [])
    has_servicer_offer = any(b.get('offered_by') == 'servicer' and float(b.get('servicer_offer_price', 0)) == 650.0 for b in b_history)
    log_result("Bargain History reflects updated Rs. 650 offer", has_servicer_offer, f"History items count: {len(b_history)}")

    # 5. Customer Counters Back with ₹580
    print("\n--- 5. CUSTOMER COUNTER-OFFERS Rs. 580 ---")
    cust_counter = {
        'appointment_id': app.id,
        'user_offer': 580.00,
        'message': 'Can we do Rs. 580?'
    }
    resp = client.post('/api/bargain/', data=json.dumps(cust_counter), content_type='application/json')
    log_result("Customer Submits Counter-Offer Rs. 580", resp.status_code == 200, f"Response: {resp.content.decode()}")
    cust_bargain_id = json.loads(resp.content.decode()).get('bargain_id')

    # 6. Servicer Accepts Customer's Counter-Offer (₹580)
    print("\n--- 6. SERVICER ACCEPTS CUSTOMER COUNTER-OFFER ---")
    client.logout()
    client.login(username="neg_servicer", password="NegSecret123!")

    resp = client.post(f'/api/bargain/{cust_bargain_id}/accept/')
    log_result("Servicer Accepts Customer Offer", resp.status_code == 200, f"Response: {resp.content.decode()}")
    app.refresh_from_db()
    log_result("Appointment Confirmed at Agreed Price (Rs. 580)", app.status == 'accepted' and float(app.expected_amount) == 580.0 and bool(app.otp), f"Final Price: Rs. {app.expected_amount}, Servicer: {app.servicer_assigned.full_name}, OTP: {app.otp}")

    # 7. Test Second Scenario: Direct Servicer Initial Price Acceptance
    print("\n--- 7. DIRECT INITIAL PRICE ACCEPTANCE WORKFLOW ---")
    client.logout()
    client.login(username="neg_customer", password="NegSecret123!")

    post_data2 = {
        'full_name': 'Negotiation Customer 2',
        'contact_number': '9811223344',
        'issue': 'electrical',
        'description': 'Light socket sparking',
        'expected_amount': '450.00',
        'address': '20 Church St',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'country': 'India',
        'pincode': '560001',
        'expected_time': future_time
    }
    client.post('/book_appointment', data=post_data2)
    app2 = Book_Appointment.objects.filter(user=cust, description__contains="Light socket sparking").order_by('-created_at').first()

    # Servicer accepts initial price directly
    client.logout()
    client.login(username="neg_servicer", password="NegSecret123!")
    resp = client.post(f'/api/appointments/{app2.id}/accept/')
    log_result("Servicer Accepts Initial Price Directly", resp.status_code == 200, f"Response: {resp.content.decode()}")
    app2.refresh_from_db()
    log_result("Direct Acceptance Status updated to 'accepted'", app2.status == 'accepted' and float(app2.expected_amount) == 450.0, f"Status: {app2.status}, Amount: Rs. {app2.expected_amount}")

    print("\n" + "=" * 70)
    print("NEGOTIATION TEST SUMMARY")
    print("=" * 70)
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"Total Negotiation Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print("=" * 70)

if __name__ == '__main__':
    test_price_negotiation()
