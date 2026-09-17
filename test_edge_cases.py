import os
import sys
import json
import django
from datetime import datetime, timedelta

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

def run_edge_case_tests():
    print("=" * 70)
    print("STARTING SKILLSETGO EDGE-CASES & ADVANCED WORKFLOW TEST SUITE")
    print("=" * 70)

    client = Client()
    results = []

    def log_result(test_name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        results.append((test_name, passed, details))
        print(f"[{status}] {test_name}: {details}")

    # 1. Test Allauth Authentication Routes
    print("\n--- 1. ALLAUTH AUTHENTICATION ROUTES ---")
    resp = client.get('/accounts/login/')
    log_result("GET /accounts/login/", resp.status_code == 200, f"Status code: {resp.status_code}")

    resp = client.get('/accounts/signup/')
    log_result("GET /accounts/signup/", resp.status_code == 200, f"Status code: {resp.status_code}")

    resp = client.get('/accounts/password/reset/')
    log_result("GET /accounts/password/reset/", resp.status_code == 200, f"Status code: {resp.status_code}")

    # 2. Test Protected Routes when Anonymous
    print("\n--- 2. ANONYMOUS ACCESS RESTRICTIONS ---")
    client.logout()

    resp = client.get('/book_appointment')
    log_result("Anonymous GET /book_appointment redirects to login", resp.status_code == 302 and '/accounts/login/' in resp.url, f"Redirect URL: {resp.url}")

    resp = client.get('/dashboard/')
    log_result("Anonymous GET /dashboard/ redirects to login", resp.status_code == 302 and '/accounts/login/' in resp.url, f"Redirect URL: {resp.url}")

    resp = client.get('/appointments/')
    log_result("Anonymous GET /appointments/ redirects to login", resp.status_code == 302 and '/accounts/login/' in resp.url, f"Redirect URL: {resp.url}")

    resp = client.get('/my_work/')
    log_result("Anonymous GET /my_work/ redirects to login", resp.status_code == 302 and '/accounts/login/' in resp.url, f"Redirect URL: {resp.url}")

    # 3. Test Customer Role Restrictions
    print("\n--- 3. CUSTOMER ROLE RESTRICTIONS ---")
    client.login(username="autotest_customer", password="TestSecret123!")

    resp = client.get('/dashboard/')
    log_result("Customer GET /dashboard/ redirects to register", resp.status_code == 302 and '/register/' in resp.url, f"Redirect URL: {resp.url}")

    resp = client.get('/bookmarked_appointments/')
    log_result("Customer GET /bookmarked_appointments/ redirects with error", resp.status_code == 302, f"Redirect URL: {resp.url}")

    resp = client.get('/generate_id_card/')
    log_result("Customer GET /generate_id_card/ forbidden (403)", resp.status_code == 403, f"Status code: {resp.status_code}")

    # 4. Test Direct Appointment Acceptance by Servicer
    print("\n--- 4. DIRECT ACCEPTANCE & BARGAIN REJECTION FLOW ---")
    future_time = (timezone.now() + timedelta(days=3)).strftime('%m/%d/%Y %I:%M %p')
    post_data = {
        'full_name': 'Direct Accept Test Customer',
        'contact_number': '9876501234',
        'issue': 'electrical',
        'description': 'Direct accept test - fuse box inspection',
        'expected_amount': '600.00',
        'address': '12 MG Road',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'country': 'India',
        'pincode': '560001',
        'expected_time': future_time
    }
    client.post('/book_appointment', data=post_data)
    direct_app = Book_Appointment.objects.filter(description__contains="fuse box inspection").order_by('-created_at').first()
    log_result("Created Direct Accept Appointment", direct_app is not None, f"ID: {direct_app.id if direct_app else 'N/A'}")

    # Servicer accepts directly at initial price
    client.logout()
    client.login(username="autotest_servicer", password="TestSecret123!")

    resp = client.post(f'/api/appointments/{direct_app.id}/accept/')
    log_result("Servicer Direct Accept API", resp.status_code == 200, f"Response: {resp.content.decode()}")
    direct_app.refresh_from_db()
    log_result("Appointment assigned & OTP generated", direct_app.status == 'accepted' and bool(direct_app.otp), f"Status: {direct_app.status}, Servicer: {direct_app.servicer_assigned.full_name}, OTP: {direct_app.otp}")

    # 5. Test Bargain Rejection Flow
    print("\n--- 5. BARGAIN REJECTION TEST ---")
    # Customer creates another appointment
    client.logout()
    client.login(username="autotest_customer", password="TestSecret123!")
    post_data2 = {
        'full_name': 'Reject Test Customer',
        'contact_number': '9876501234',
        'issue': 'cleaning',
        'description': 'Deep cleaning kitchen floor and tiles',
        'expected_amount': '400.00',
        'address': '55 Indiranagar 100ft Rd',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'country': 'India',
        'pincode': '560038',
        'expected_time': future_time
    }
    client.post('/book_appointment', data=post_data2)
    reject_app = Book_Appointment.objects.filter(description__contains="Deep cleaning kitchen floor").order_by('-created_at').first()

    # Servicer offers counter price
    client.logout()
    client.login(username="autotest_servicer", password="TestSecret123!")
    bargain_payload = {
        'appointment_id': reject_app.id,
        'servicer_offer': 700.00,
        'message': 'Requires heavy chemical scrub.'
    }
    resp = client.post('/api/bargain/', data=json.dumps(bargain_payload), content_type='application/json')
    bargain_id = json.loads(resp.content.decode()).get('bargain_id')

    # Customer rejects offer
    client.logout()
    client.login(username="autotest_customer", password="TestSecret123!")
    resp = client.post(f'/api/bargain/{bargain_id}/reject/')
    log_result("Customer Rejects Bargain Offer", resp.status_code == 200, f"Response: {resp.content.decode()}")
    reject_bargain = Bargaining.objects.get(id=bargain_id)
    log_result("Bargain status marked 'rejected'", reject_bargain.status == 'rejected', f"Bargain status: {reject_bargain.status}")

    # 6. Test Bookmark Toggle (Unbookmark)
    print("\n--- 6. BOOKMARK TOGGLE (REMOVE) ---")
    client.logout()
    client.login(username="autotest_servicer", password="TestSecret123!")

    # Unbookmark the appointment from previous test
    resp = client.post(f'/api/appointments/{direct_app.id}/bookmark/')
    log_result("Servicer Bookmark direct_app (Add)", resp.status_code == 200 and json.loads(resp.content.decode())['bookmarked'] is True, f"Response: {resp.content.decode()}")
    resp = client.post(f'/api/appointments/{direct_app.id}/bookmark/')
    log_result("Servicer Bookmark direct_app (Remove)", resp.status_code == 200 and json.loads(resp.content.decode())['bookmarked'] is False, f"Response: {resp.content.decode()}")

    # 7. Summary
    print("\n" + "=" * 70)
    print("EDGE-CASES TEST SUMMARY")
    print("=" * 70)
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"Total Edge-Cases Tested: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print("=" * 70)

if __name__ == '__main__':
    run_edge_case_tests()
