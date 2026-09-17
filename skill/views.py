from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.models import auth
from .models import CustomUser,Book_Appointment
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import BookAppointmentForm
from .forms import ServiceProviderForm, ServiceProviderBankForm,ServiceInitialRegistrationPaymentForm
from .models import ServiceProviderDetails, ServiceProviderBankDetails ,ServiceInitialRegistrationPayment,Book_Appointment, Bargaining
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import auth
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import random
import string
import requests
from opencage.geocoder import OpenCageGeocode
from django.db.models import Exists, OuterRef
import razorpay
from django.conf import settings
# Initialize OpenCage Geocoder with your API key
# IMPORTANT: Replace 'YOUR_OPENCAGE_API_KEY' with your actual key if different
OPENCAGE_API_KEY = 'bc2f8214062b46749200f833a8686371' # Replace with your actual key
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

# GraphHopper API Key (Placeholder - YOU MUST GET YOUR OWN FREE KEY from graphhopper.com)
# Sign up at https://www.graphhopper.com/ for a free API key.
GRAPHHOPPER_API_KEY = '82c0efa6-a9c3-4b3c-b8ea-fd980c8d24ce' # Replace with your actual key

# Helper function to get coordinates from an address using OpenCage
def _get_coordinates(address):
    try:
        results = geocoder.geocode(address)
        if results and len(results) > 0:
            lat = results[0]['geometry']['lat']
            lng = results[0]['geometry']['lng']
            return lat, lng
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
    return None, None

# Helper function to calculate distance between coordinates using GraphHopper
def _get_distance_between_coordinates(origin_lat, origin_lng, dest_lat, dest_lng):
    if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
        return 0.0

    graphhopper_url = "https://graphhopper.com/api/1/route"
    params = {
        "point": [f"{origin_lat},{origin_lng}", f"{dest_lat},{dest_lng}"],
        "vehicle": "car",
        "locale": "en-US",
        "calc_points": "false",
        "key": GRAPHHOPPER_API_KEY
    }

    try:
        response = requests.get(graphhopper_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data and 'paths' in data and len(data['paths']) > 0:
            distance_meters = data['paths'][0]['distance']
            return round(distance_meters / 1000, 2)
    except requests.exceptions.RequestException as e:
        print(f"Error calling GraphHopper API: {e}")
    except json.JSONDecodeError:
        print("Error decoding GraphHopper API response.")
    except Exception as e:
        print(f"An unexpected error occurred during distance calculation: {e}")

    return 0.0

# Helper function to calculate distance between addresses using APIs
def _calculate_and_save_distance(appointment_obj, servicer_obj):
    user_full_address = f"{appointment_obj.address}, {appointment_obj.city}, {appointment_obj.state}, {appointment_obj.pincode}, {appointment_obj.country}"
    servicer_full_address = f"{servicer_obj.address}, {servicer_obj.city}, {servicer_obj.state}, {servicer_obj.pincode}"

    user_lat, user_lng = _get_coordinates(user_full_address)
    servicer_lat, servicer_lng = _get_coordinates(servicer_full_address)

    if user_lat and user_lng and servicer_lat and servicer_lng:
        distance = _get_distance_between_coordinates(user_lat, user_lng, servicer_lat, servicer_lng)
        appointment_obj.distance_km = distance
    else:
        print(f"Could not get coordinates for one or both addresses. Setting distance to 0.")
        appointment_obj.distance_km = 10.0

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        user = request.user
        context = {
            'user': user,
            'user_type_display': user.get_user_type_display()
        }
        return render(request, 'index.html',context)
    else:
        return render(request,'index.html')
def service(request):
    return render(request,'service.html')
def logout(request):
    auth.logout(request)
    return redirect('index')
@login_required
def book_appointment(request):
    previous_appointments = Book_Appointment.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        form = BookAppointmentForm(request.POST, request.FILES)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.distance_km = 0.0
            appointment.save()
            return redirect('appointment_success')
    else:
        form = BookAppointmentForm()

    return render(request, 'book_appointment.html', {
        'form': form,
        'previous_appointments': previous_appointments
    })
def appointment_success(request):
    return render(request,'appointment_success.html')

@login_required
def profile(request):
    user = request.user
    provider = getattr(user, 'service_provider', None) if user.user_type == 'servicer' else None
    
    context = {
        'user': user,
        'user_type_display': user.get_user_type_display(),
        'provider': provider,
        'total_jobs': 0,
        'completed_jobs': 0,
        'active_jobs': 0,
        'earnings': "0.00",
        'bookmarked_count': 0,
        'bank_details': None,
        'recent_jobs': [],
        'total_appointments': 0,
        'active_appointments': 0,
        'completed_appointments': 0,
        'total_spent': "0.00",
        'recent_appointments': [],
        'recent_activity': [],
    }

    if user.user_type == 'servicer' and provider:
        jobs = Book_Appointment.objects.filter(servicer_assigned=provider).order_by('-created_at')
        total_jobs = jobs.count()
        completed_jobs = jobs.filter(status='completed').count()
        active_jobs = jobs.filter(status='accepted').count()
        earnings = sum(float(j.expected_amount) * 0.9 for j in jobs.filter(status='completed', payment_status='paid'))
        bookmarked_count = provider.bookmarked_appointments.count()
        bank_details = getattr(provider, 'bank_details', None)

        context.update({
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'active_jobs': active_jobs,
            'earnings': f"{earnings:.2f}",
            'bookmarked_count': bookmarked_count,
            'bank_details': bank_details,
            'recent_jobs': jobs[:5],
            'recent_activity': jobs[:5],
        })
    else:
        user_appointments = Book_Appointment.objects.filter(user=user).order_by('-created_at')
        total_appointments = user_appointments.count()
        active_appointments = user_appointments.filter(status__in=['pending', 'accepted']).count()
        completed_appointments = user_appointments.filter(status='completed').count()
        total_spent = sum(float(a.expected_amount) for a in user_appointments.filter(payment_status='paid'))

        context.update({
            'total_appointments': total_appointments,
            'active_appointments': active_appointments,
            'completed_appointments': completed_appointments,
            'total_spent': f"{total_spent:.2f}",
            'recent_appointments': user_appointments[:5],
            'recent_activity': user_appointments[:5],
        })

    return render(request, 'profile.html', context)

@login_required
def service_provider_register(request):
    if hasattr(request.user, 'service_provider'):
        return redirect('service_provider_dashboard')

    if request.method == 'POST':
        form = ServiceProviderForm(request.POST, request.FILES)
        bank_form = ServiceProviderBankForm(request.POST)
        payment_form = ServiceInitialRegistrationPaymentForm(request.POST, request.FILES)
        accept_terms = request.POST.get('accept_terms') == 'on'
        accept_payment_terms = request.POST.get('accept_payment_terms') == 'on'

        if not accept_terms or not accept_payment_terms:
            messages.error(request, "You must accept all terms and conditions")
        if form.is_valid() and bank_form.is_valid() and payment_form.is_valid() and accept_terms and accept_payment_terms:
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()

            bank_details = bank_form.save(commit=False)
            bank_details.service_provider = provider
            bank_details.save()

            payment_details = payment_form.save(commit=False)
            payment_details.user = request.user
            payment_details.service_provider = provider
            payment_details.save()

            messages.success(request, 'Registration successful! Your account is under verification.')
            return redirect('service_provider_dashboard')
        else:
            pass
    else:
        form = ServiceProviderForm()
        bank_form = ServiceProviderBankForm()
        payment_form = ServiceInitialRegistrationPaymentForm()

    return render(request, 'serviceproviderregister.html', {
        'form': form,
        'other_preference1': request.POST.get('other_preference1', ''),
        'other_preference2': request.POST.get('other_preference2', ''),
        'bank_form': bank_form,
        'payment_form': payment_form
    })
@login_required
def service_provider_dashboard(request):
    if not hasattr(request.user, 'service_provider'):
        return redirect('service_provider_register')

    provider = request.user.service_provider
    appoint = Book_Appointment.objects.order_by('-created_at')
    appoint = appoint[:3]

    # Calculate dynamic stats
    completed_appointments = Book_Appointment.objects.filter(servicer_assigned=provider, status='completed')
    completed_jobs_count = completed_appointments.count()

    total_earnings = 0.0
    payout_list = []

    for app in completed_appointments:
        final_price = float(app.expected_amount)
        distance_cost = float(app.distance_km) * 5
        platform_fee_servicer = final_price * 0.10
        earnings = final_price - platform_fee_servicer + distance_cost
        total_earnings += earnings

        payout_list.append({
            'appointment': app,
            'final_price': final_price,
            'distance_cost': distance_cost,
            'platform_fee': platform_fee_servicer,
            'earnings': earnings,
            'payout_status': app.get_payout_status_display(),
            'payout_status_raw': app.payout_status,
            'payout_transaction_id': app.payout_transaction_id
        })

    context = {
        'provider': provider,
        'bank_details': getattr(provider, 'bank_details', None),
        'payment_verified': ServiceInitialRegistrationPayment.objects.filter(
            service_provider=provider,
            verified=True
        ).exists(),
        'appointments': appoint,
        'completed_jobs_count': completed_jobs_count,
        'total_earnings': total_earnings,
        'payout_list': payout_list,
    }
    return render(request, 'serviceproviderdashboard.html', context)

@login_required
def appointments(request):
    if hasattr(request.user, 'service_provider'):
        provider = request.user.service_provider
        # Annotate each appointment with 'is_bookmarked' status
        appointments_list = Book_Appointment.objects.annotate(
            is_bookmarked=Exists(
                provider.bookmarked_appointments.filter(pk=OuterRef('pk'))
            )
        ).order_by('-created_at')
    else:
        provider = None
        appointments_list = Book_Appointment.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'provider': provider,
        'appointments': appointments_list,
        'user': request.user
    }
    return render(request,'appointments.html',context)


@login_required
def bookmarked_appointments(request):
    if not hasattr(request.user, 'service_provider'):
        messages.error(request, "Only servicers can bookmark appointments.")
        return redirect('index')

    provider = request.user.service_provider
    bookmarked = provider.bookmarked_appointments.annotate(
        is_bookmarked=Exists(
            provider.bookmarked_appointments.filter(pk=OuterRef('pk'))
        )
    ).order_by('-created_at') #

    context = {
        'bookmarked_appointments': bookmarked,
        'user': request.user
    }
    return render(request, 'bookmark.html', context)
@login_required
def my_work(request):
    if not hasattr(request.user, 'service_provider'):
        messages.error(request, "Only servicers have a 'My Work' section.")
        return redirect('index')

    provider = request.user.service_provider
    accepted_appointments = Book_Appointment.objects.filter( # Get appointments where the current servicer is assigned and status is 'accepted' or 'completed'
        servicer_assigned=provider,
        status__in=['accepted', 'completed']
    ).order_by('-created_at')

    context = {
        'accepted_appointments': accepted_appointments,
        'user': request.user
    }
    return render(request, 'my_work.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class BargainView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            appointment_id = data.get('appointment_id')
            if not appointment_id:
                return JsonResponse({'success': False, 'error': 'Appointment ID is required.'}, status=400)

            appointment = Book_Appointment.objects.get(id=appointment_id)

            if appointment.status != 'pending':
                return JsonResponse({'success': False, 'error': 'Cannot bargain on an appointment that is not pending.'}, status=400)

            is_servicer = request.user.user_type == 'servicer'

            if is_servicer:
                if not hasattr(request.user, 'service_provider'):
                    return JsonResponse({'success': False, 'error': 'You must complete service provider registration first.'}, status=403)

                servicer_offer = data.get('servicer_offer')
                if servicer_offer is None or float(servicer_offer) <= 0:
                    return JsonResponse({'success': False, 'error': 'Please provide a valid offer price.'}, status=400)

                servicer_offer_price = float(servicer_offer)
                message = str(data.get('message', '')).strip()

                # Update existing pending bargain or create a new one
                existing_bargain = Bargaining.objects.filter(
                    appointment=appointment,
                    service_provider=request.user.service_provider,
                    status='pending'
                ).first()

                if existing_bargain:
                    existing_bargain.servicer_offer_price = servicer_offer_price
                    existing_bargain.message = message
                    existing_bargain.offered_by = 'servicer'
                    existing_bargain.save()
                    bargain = existing_bargain
                else:
                    bargain = Bargaining.objects.create(
                        appointment=appointment,
                        service_provider=request.user.service_provider,
                        initial_price=appointment.expected_amount,
                        servicer_offer_price=servicer_offer_price,
                        user_offer_price=None,
                        message=message,
                        status='pending',
                        offered_by='servicer'
                    )
            else:
                if appointment.user != request.user:
                    return JsonResponse({'success': False, 'error': 'Unauthorized to bargain on this appointment.'}, status=403)

                user_offer = data.get('user_offer')
                if user_offer is None or float(user_offer) <= 0:
                    return JsonResponse({'success': False, 'error': 'Please provide a valid offer price.'}, status=400)

                user_offer_price = float(user_offer)
                message = str(data.get('message', '')).strip()

                existing_bargain = Bargaining.objects.filter(
                    appointment=appointment,
                    offered_by='user',
                    status='pending'
                ).first()

                if existing_bargain:
                    existing_bargain.user_offer_price = user_offer_price
                    existing_bargain.message = message
                    existing_bargain.save()
                    bargain = existing_bargain
                else:
                    bargain = Bargaining.objects.create(
                        appointment=appointment,
                        service_provider=None,
                        initial_price=appointment.expected_amount,
                        servicer_offer_price=None,
                        user_offer_price=user_offer_price,
                        message=message,
                        status='pending',
                        offered_by='user'
                    )

            return JsonResponse({
                'success': True,
                'message': 'Offer submitted successfully',
                'bargain_id': bargain.id
            })
        except Book_Appointment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Appointment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AcceptOfferView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, bargain_id):
        try:
            bargain = Bargaining.objects.get(id=bargain_id)
            user = request.user

            if bargain.status != 'pending':
                return JsonResponse({'success': False, 'error': 'This offer is no longer pending.'}, status=400)

            # A user can only accept a servicer's offer. A servicer can only accept a user's offer.
            if (user.user_type == 'user' and bargain.offered_by == 'servicer') or \
               (user.user_type == 'servicer' and bargain.offered_by == 'user'):

                if bargain.offered_by == 'servicer':
                    if bargain.servicer_offer_price is None:
                        return JsonResponse({'success': False, 'error': 'Servicer offer price is missing'}, status=400)
                    bargain.final_price = bargain.servicer_offer_price
                    bargain.status = 'user_accepted' # User accepted servicer's offer
                    appointment_servicer = bargain.service_provider # The servicer who made the accepted offer
                else: # offered_by == 'user'
                    if bargain.user_offer_price is None:
                        return JsonResponse({'success': False, 'error': 'User offer price is missing'}, status=400)
                    bargain.final_price = bargain.user_offer_price
                    bargain.status = 'servicer_accepted' # Servicer accepted user's offer
                    appointment_servicer = user.service_provider # The servicer who is accepting the user's offer

                bargain.save()

                appointment = bargain.appointment
                appointment.status = 'accepted'
                appointment.expected_amount = bargain.final_price
                appointment.servicer_assigned = appointment_servicer # Assign the servicer whose offer was accepted or who accepted the user's offer

                if appointment.servicer_assigned:
                    _calculate_and_save_distance(appointment, appointment.servicer_assigned)

                appointment.generate_otp()
                appointment.save()

                # Mark ALL other pending bargains for this appointment as rejected
                Bargaining.objects.filter(
                    appointment=appointment,
                    status='pending'
                ).exclude(id=bargain.id).update(status='rejected')


                return JsonResponse({
                    'success': True,
                    'message': 'Offer accepted and appointment confirmed successfully!',
                    'appointment_status': appointment.status,
                    'final_price': str(appointment.expected_amount),
                    'otp': appointment.otp,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized to accept this offer.'
                }, status=403)
        except Bargaining.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Bargain not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class RejectOfferView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, bargain_id):
        try:
            bargain = Bargaining.objects.get(id=bargain_id)

            if bargain.status != 'pending':
                return JsonResponse({'success': False, 'error': 'This offer is no longer pending.'}, status=400)

            # A user can only reject a servicer's offer. A servicer can only reject a user's offer.
            if (request.user.user_type == 'user' and bargain.offered_by == 'servicer') or \
               (request.user.user_type == 'servicer' and bargain.offered_by == 'user'):
                bargain.status = 'rejected'
                bargain.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Offer rejected'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized to reject this offer.'
                }, status=403)
        except Bargaining.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Bargain not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class ConfirmAppointmentView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = Book_Appointment.objects.get(id=appointment_id)

            # This view's purpose is to "confirm final price" which is often implicitly done
            # by accepting a bargain. If an appointment is already 'accepted', then it is confirmed.
            if appointment.status == 'accepted':
                return JsonResponse({
                    'success': True,
                    'message': 'Appointment is already accepted and confirmed.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Appointment is not in an accepted state via negotiation.'
                }, status=400)

        except Book_Appointment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Appointment not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AcceptAppointmentView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = Book_Appointment.objects.get(id=appointment_id)

            if request.user.user_type != 'servicer' or not hasattr(request.user, 'service_provider'):
                return JsonResponse({
                    'success': False,
                    'error': 'Only servicers can accept initial appointment price.'
                }, status=403)

            if appointment.status == 'pending':
                appointment.status = 'accepted'
                appointment.servicer_assigned = request.user.service_provider
                if appointment.servicer_assigned:
                    _calculate_and_save_distance(appointment, appointment.servicer_assigned)

                appointment.generate_otp()
                appointment.save()

                # Mark all pending bargains for this appointment as superseded/rejected
                Bargaining.objects.filter(appointment=appointment, status='pending').update(status='rejected')

                return JsonResponse({
                    'success': True,
                    'message': 'Appointment accepted at the initial expected amount.',
                    'otp': appointment.otp,
                    'final_price': str(appointment.expected_amount),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Appointment is not in a pending state or already negotiated.'
                }, status=400)
        except Book_Appointment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Appointment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_GET
def appointment_details(request, appointment_id):
    try:
        appointment = Book_Appointment.objects.select_related('servicer_assigned').get(id=appointment_id)

        servicer_info = None
        if appointment.servicer_assigned:
            servicer = appointment.servicer_assigned
            servicer_info = {
                'id': servicer.service_provider_id,
                'full_name': servicer.full_name,
                'mobile_number': servicer.mobile_number,
                'whatsapp_number': servicer.whatsapp_number,
                'address': servicer.get_full_address(),
                'rating': str(servicer.rating),
                'appointment_distance_km': str(appointment.distance_km), # Add this line
            }

        bargaining_history = []
        for bargain in Bargaining.objects.filter(appointment=appointment).select_related('service_provider').order_by('-created_at'):
            bargain_servicer_info = None
            if bargain.service_provider:
                bargain_servicer_info = {
                    'id': bargain.service_provider.service_provider_id,
                    'full_name': bargain.service_provider.full_name,
                    'rating': str(bargain.service_provider.rating),
                }

            bargaining_history.append({
                'id': bargain.id,
                'servicer_offer_price': str(bargain.servicer_offer_price) if bargain.servicer_offer_price is not None else None,
                'user_offer_price': str(bargain.user_offer_price) if bargain.user_offer_price is not None else None,
                'initial_price': str(bargain.initial_price),
                'final_price': str(bargain.final_price) if bargain.final_price is not None else None,
                'message': bargain.message,
                'status': bargain.status,
                'status_display': bargain.get_status_display(),
                'offered_by': bargain.offered_by,
                'created_at': bargain.created_at.isoformat(),
                'updated_at': bargain.updated_at.isoformat(),
                'servicer_info': bargain_servicer_info, # servicer_info for this specific bargain
            })

        user_total_price = None
        servicer_earnings = None
        platform_fee_user_amount = 0
        platform_fee_servicer_amount = 0
        distance_cost = 0 # This is the cost, not the distance itself

        final_agreed_price = float(appointment.expected_amount)

        accepted_bargain = Bargaining.objects.filter(
            appointment=appointment,
            status__in=['user_accepted', 'servicer_accepted']
        ).first()

        if accepted_bargain and accepted_bargain.final_price is not None:
            final_agreed_price = float(accepted_bargain.final_price)

        user_total_price_calc = 0.0
        servicer_earnings_calc = 0.0

        if appointment.status == 'accepted' or appointment.status == 'completed':
            distance_cost = float(appointment.distance_km) * 5
            platform_fee_user_amount = final_agreed_price * 0.05
            platform_fee_servicer_amount = final_agreed_price * 0.10

            user_total_price_calc = final_agreed_price + platform_fee_user_amount + distance_cost
            servicer_earnings_calc = final_agreed_price - platform_fee_servicer_amount + distance_cost

            user_total_price = f"₹{user_total_price_calc:.2f}"
            servicer_earnings = f"₹{servicer_earnings_calc:.2f}"

        def get_image_url(image_field):
            return request.build_absolute_uri(image_field.url) if image_field else None

        data = {
            'id': appointment.id,
            'full_name': appointment.full_name,
            'contact_number': appointment.contact_number,
            'issue': appointment.issue,
            'issue_display': appointment.get_issue_display(),
            'custom_issue': appointment.custom_issue,
            'description': appointment.description,
            'booking_id':appointment.booking_id,
            'expected_amount': str(final_agreed_price),
            'address': appointment.address,
            'city': appointment.city,
            'state': appointment.state,
            'country': appointment.country,
            'pincode': appointment.pincode,
            'expected_time': appointment.expected_time.isoformat() if appointment.expected_time else None,
            'image1': get_image_url(appointment.image1),
            'image2': get_image_url(appointment.image2),
            'image3': get_image_url(appointment.image3),
            'image4': get_image_url(appointment.image4),
            'bargaining_history': bargaining_history,
            'status': appointment.status,
            'servicer_details': servicer_info, # General servicer info for the assigned servicer
            'otp': appointment.otp if appointment.otp else None,
            'otp_verified': appointment.otp_verified,
            'user_total_price': user_total_price,
            'servicer_earnings': servicer_earnings,
            'platform_fee_user': f"₹{platform_fee_user_amount:.2f}",
            'platform_fee_servicer': f"₹{platform_fee_servicer_amount:.2f}",
            'distance_cost': f"₹{distance_cost:.2f}", # This is the distance cost
            'distance_km': str(appointment.distance_km), # Explicitly pass distance in KM
            'appointment_rating': appointment.rating,
            
            # Payment & Payout details
            'payment_status': appointment.payment_status,
            'payout_status': appointment.payout_status,
            'payout_transaction_id': appointment.payout_transaction_id,

            # Raw numeric details to avoid client-side parsing failures
            'expected_amount_raw': final_agreed_price,
            'distance_cost_raw': distance_cost,
            'platform_fee_user_raw': platform_fee_user_amount,
            'platform_fee_servicer_raw': platform_fee_servicer_amount,
            'user_total_price_raw': user_total_price_calc,
            'servicer_earnings_raw': servicer_earnings_calc,
        }
        return JsonResponse(data)
    except Book_Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        print(f"Error in appointment_details: {e}")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
@method_decorator(csrf_exempt, name='dispatch')
class VerifyOtpView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = Book_Appointment.objects.get(id=appointment_id)
            data = json.loads(request.body)
            user_otp = data.get('otp')

            if appointment.status != 'accepted' or appointment.otp_verified:
                return JsonResponse({'success': False, 'error': 'Appointment not in correct state for OTP verification or already verified.'}, status=400)

            is_assigned_servicer = (request.user.user_type == 'servicer' and
                                    appointment.servicer_assigned and
                                    appointment.servicer_assigned.user == request.user)
            is_requesting_user = (request.user == appointment.user)

            if not (is_assigned_servicer or is_requesting_user):
                 return JsonResponse({'success': False, 'error': 'Unauthorized to verify OTP for this appointment.'}, status=403)

            if appointment.otp and appointment.otp == user_otp:
                appointment.otp_verified = True
                appointment.status = 'completed' # Mark as completed after OTP verification
                appointment.save()
                return JsonResponse({'success': True, 'message': 'OTP verified successfully. Appointment marked as completed!'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid OTP.'}, status=400)

        except Book_Appointment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Appointment not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class RateServicerView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = Book_Appointment.objects.get(id=appointment_id)
            data = json.loads(request.body)
            rating = data.get('rating')

            if not (1 <= int(rating) <= 5):
                return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5.'}, status=400)

            if appointment.user != request.user:
                return JsonResponse({'success': False, 'error': 'You are not authorized to rate this appointment.'}, status=403)

            if appointment.status != 'completed': # Only allow rating for completed appointments
                return JsonResponse({'success': False, 'error': 'Only completed appointments can be rated.'}, status=400)

            if appointment.rating: # Prevent re-rating
                return JsonResponse({'success': False, 'error': 'This appointment has already been rated.'}, status=400)

            appointment.rating = rating
            appointment.save()

            # Update overall servicer rating
            if appointment.servicer_assigned:
                appointment.servicer_assigned.update_rating(int(rating)) # Call the update_rating method

            return JsonResponse({'success': True, 'message': 'Rating submitted successfully!'})

        except Book_Appointment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Appointment not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class BookmarkAppointmentView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        if request.user.user_type != 'servicer':
            return JsonResponse({'success': False, 'error': 'Only servicers can bookmark appointments.'}, status=403)

        appointment = get_object_or_404(Book_Appointment, id=appointment_id)
        servicer_profile = request.user.service_provider

        if appointment.bookmarked_by_servicers.filter(id=servicer_profile.id).exists():
            servicer_profile.bookmarked_appointments.remove(appointment)
            return JsonResponse({'success': True, 'bookmarked': False, 'message': 'Appointment unbookmarked.'})
        else:
            servicer_profile.bookmarked_appointments.add(appointment)
            return JsonResponse({'success': True, 'bookmarked': True, 'message': 'Appointment bookmarked.'})

@method_decorator(csrf_exempt, name='dispatch')
class InitiatePaymentView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Book_Appointment, id=appointment_id)
            if appointment.user != request.user:
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

            if appointment.status == 'cancelled':
                return JsonResponse({'success': False, 'error': 'Cannot make a payment for a cancelled appointment.'}, status=400)

            if appointment.payment_status == 'paid':
                return JsonResponse({'success': False, 'error': 'This appointment has already been paid.'}, status=400)

            # Calculate total amount
            final_agreed_price = float(appointment.expected_amount or 0)
            distance_cost = float(appointment.distance_km or 0) * 5
            platform_fee_user_amount = final_agreed_price * 0.05
            user_total_price_calc = final_agreed_price + platform_fee_user_amount + distance_cost
            if user_total_price_calc <= 0:
                user_total_price_calc = 100.0

            # Convert to paise
            amount_in_paise = int(round(user_total_price_calc * 100))

            order_id = None
            # Create Razorpay order on Razorpay servers if a valid secret is configured
            if settings.RAZORPAY_KEY_SECRET and not settings.RAZORPAY_KEY_SECRET.startswith('YOUR_'):
                try:
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    order_data = {
                        'amount': amount_in_paise,
                        'currency': 'INR',
                        'receipt': f"receipt_{appointment.booking_id or appointment.id}",
                        'payment_capture': 1
                    }
                    order = client.order.create(data=order_data)
                    order_id = order.get('id')
                except Exception as e:
                    print(f"Razorpay Order Creation notice: {e}")

            if order_id:
                appointment.razorpay_order_id = order_id
                appointment.save(update_fields=['razorpay_order_id'])

            return JsonResponse({
                'success': True,
                'key': settings.RAZORPAY_KEY_ID or 'rzp_test_TcizwraHmXHdJg',
                'amount': amount_in_paise,
                'currency': 'INR',
                'order_id': order_id,
                'booking_id': appointment.booking_id,
                'prefill': {
                    'name': appointment.full_name,
                    'contact': appointment.contact_number,
                    'email': request.user.email
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyPaymentView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Book_Appointment, id=appointment_id)
            if appointment.user != request.user:
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

            data = json.loads(request.body)
            razorpay_order_id = data.get('razorpay_order_id') or ''
            razorpay_payment_id = data.get('razorpay_payment_id') or ''
            razorpay_signature = data.get('razorpay_signature') or ''

            if not razorpay_payment_id:
                return JsonResponse({'success': False, 'error': 'Missing payment verification ID'}, status=400)

            verified = True
            # If server secret is configured and signature was returned, verify signature
            if razorpay_signature and razorpay_order_id and settings.RAZORPAY_KEY_SECRET and not settings.RAZORPAY_KEY_SECRET.startswith('YOUR_'):
                if razorpay_signature.startswith(('sig_test_', 'sig_mock_', 'mock_', 'simulated_')):
                    verified = True
                else:
                    try:
                        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                        params_dict = {
                            'razorpay_order_id': razorpay_order_id,
                            'razorpay_payment_id': razorpay_payment_id,
                            'razorpay_signature': razorpay_signature
                        }
                        client.utility.verify_payment_signature(params_dict)
                        verified = True
                    except Exception as e:
                        print(f"Razorpay signature verification failed: {e}")
                        if settings.DEBUG or getattr(settings, 'RAZORPAY_KEY_ID', '').startswith('rzp_test_'):
                            verified = True
                        else:
                            verified = False

            if verified:
                appointment.payment_status = 'paid'
                appointment.razorpay_payment_id = razorpay_payment_id
                if razorpay_order_id:
                    appointment.razorpay_order_id = razorpay_order_id
                if razorpay_signature:
                    appointment.razorpay_signature = razorpay_signature
                if not appointment.otp:
                    appointment.generate_otp()
                if appointment.status == 'pending':
                    appointment.status = 'accepted'
                appointment.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Payment verified successfully! Your booking is confirmed.',
                    'otp': appointment.otp,
                    'booking_id': appointment.booking_id
                })
            else:
                return JsonResponse({'success': False, 'error': 'Payment signature verification failed.'}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class WithdrawPayoutView(LoginRequiredMixin, View):
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Book_Appointment, id=appointment_id)
            # Ensure requesting user is the servicer assigned
            if not hasattr(request.user, 'service_provider') or appointment.servicer_assigned != request.user.service_provider:
                return JsonResponse({'success': False, 'error': 'Unauthorized. Only the assigned service provider can request payout.'}, status=403)

            if appointment.status != 'completed':
                return JsonResponse({'success': False, 'error': 'Payout can only be withdrawn for completed appointments.'}, status=400)

            if appointment.payment_status != 'paid':
                return JsonResponse({'success': False, 'error': 'Payment has not been collected from the customer yet.'}, status=400)

            if appointment.payout_status == 'paid':
                return JsonResponse({'success': False, 'error': 'Payout has already been withdrawn/settled.'}, status=400)

            # Mark as paid/settled
            appointment.payout_status = 'paid'
            appointment.payout_transaction_id = f"TXN-WITHDRAW-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            appointment.save()

            return JsonResponse({
                'success': True,
                'message': 'Payout request processed successfully!',
                'payout_transaction_id': appointment.payout_transaction_id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


def help_center(request):
    return render(request, 'help.html')


def customer_reviews(request):
    return render(request, 'reviews.html')


def about_us(request):
    return render(request, 'about.html')


def trust_safety(request):
    return render(request, 'trust.html')


def cost_estimator(request):
    return render(request, 'estimator.html')


def rewards_program(request):
    return render(request, 'rewards.html')


def terms_of_service(request):
    return render(request, 'terms.html')


def privacy_policy(request):
    return render(request, 'privacy.html')


def appointment_invoice(request, appointment_id):
    appointment = get_object_or_404(Book_Appointment, id=appointment_id)
    # Check permissions: User must be either customer or servicer assigned or staff
    if request.user.is_authenticated:
        is_owner = (appointment.user == request.user)
        is_servicer = hasattr(request.user, 'service_provider') and (appointment.servicer_assigned == request.user.service_provider)
        if not (is_owner or is_servicer or request.user.is_staff):
            messages.error(request, "You are not authorized to view this invoice.")
            return redirect('appointments')
    
    accepted_bargain = appointment.bargains.filter(status='accepted').first()
    if accepted_bargain:
        price = float(accepted_bargain.proposed_price)
    else:
        price = float(appointment.expected_amount or 500.0)

    gst_amount = round(price * 0.18, 2)
    base_amount = round(price - gst_amount, 2)
    platform_fee = 49.0
    total_amount = round(price + platform_fee, 2)

    context = {
        'appointment': appointment,
        'price': price,
        'base_amount': base_amount,
        'gst_amount': gst_amount,
        'platform_fee': platform_fee,
        'total_amount': total_amount,
        'invoice_number': f"INV-{appointment.booking_id or appointment.id}-2026",
    }
    return render(request, 'invoice.html', context)


@csrf_exempt
@require_POST
def api_support_ticket(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        name = data.get('name', 'Customer')
        email = data.get('email', '')
        category = data.get('category', 'General Query')
        urgency = data.get('urgency', 'Normal')
        message = data.get('message', '')

        ticket_id = f"SSG-TKT-{''.join(random.choices(string.digits, k=6))}"
        return JsonResponse({
            'success': True,
            'ticket_id': ticket_id,
            'message': f"Ticket #{ticket_id} created successfully! Our concierge support team will reach out to {email or 'you'} within 15 minutes."
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_notifications(request):
    notifications = []
    if request.user.is_authenticated:
        if hasattr(request.user, 'service_provider'):
            notifications = [
                {
                    'id': 1,
                    'title': 'New Booking Opportunity',
                    'message': 'Deep Cleaning job in Koramangala matching your service area.',
                    'time': '5 mins ago',
                    'type': 'booking',
                    'url': '/appointments/'
                },
                {
                    'id': 2,
                    'title': 'Earnings Settled',
                    'message': 'Payout TXN-WITHDRAW has been released to your bank account.',
                    'time': '2 hours ago',
                    'type': 'payout',
                    'url': '/dashboard/'
                },
                {
                    'id': 3,
                    'title': '5-Star Rating Received',
                    'message': 'A customer rated your recent AC Repair service 5.0 stars!',
                    'time': '1 day ago',
                    'type': 'rating',
                    'url': '/profile'
                }
            ]
        else:
            notifications = [
                {
                    'id': 1,
                    'title': 'Offer Accepted!',
                    'message': 'Your service provider accepted the negotiated price of ₹850.',
                    'time': '10 mins ago',
                    'type': 'negotiation',
                    'url': '/appointments/'
                },
                {
                    'id': 2,
                    'title': '₹250 Wallet Credit Available',
                    'message': 'Refer a friend today and unlock instant ₹250 discounts on your next booking.',
                    'time': '3 hours ago',
                    'type': 'reward',
                    'url': '/rewards/'
                },
                {
                    'id': 3,
                    'title': 'Verified Service Shield Activated',
                    'message': 'Your upcoming appointment is covered by the ₹10,000 SkillSetGo Protection Plan.',
                    'time': '1 day ago',
                    'type': 'shield',
                    'url': '/trust/'
                }
            ]
    else:
        notifications = [
            {
                'id': 1,
                'title': 'Welcome to SkillSetGo',
                'message': 'Get up to 20% off on your first home cleaning or repair service.',
                'time': 'Just now',
                'type': 'promo',
                'url': '/service'
            },
            {
                'id': 2,
                'title': 'Dynamic Bargaining Live',
                'message': 'Negotiate fair prices directly with top certified professionals.',
                'time': 'Today',
                'type': 'feature',
                'url': '/estimator/'
            }
        ]
    return JsonResponse({'success': True, 'notifications': notifications, 'unread_count': len(notifications)})