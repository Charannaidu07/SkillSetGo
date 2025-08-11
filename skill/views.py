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
    context = {
        'user': user,
        'user_type_display': user.get_user_type_display()
    }
    return render(request,'profile.html',context)

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
    appoint=Book_Appointment.objects.order_by('-created_at')
    appoint=appoint[:3]
    context = {
        'provider': provider,
        'bank_details': getattr(provider, 'bank_details', None),
        'payment_verified': ServiceInitialRegistrationPayment.objects.filter(
            service_provider=provider,
            verified=True
        ).exists(),
        'appointments':appoint,
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
    # Apply require_POST to dispatch method to ensure it's processed correctly
    @method_decorator(require_POST, name='dispatch')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            appointment = Book_Appointment.objects.get(id=data['appointment_id'])

            if appointment.status != 'pending':
                return JsonResponse({'success': False, 'error': 'Cannot bargain on an appointment that is not pending.'}, status=400)

            is_servicer = request.user.user_type == 'servicer'

            # Allow multiple pending offers, but only one from the current servicer/user
            if is_servicer and Bargaining.objects.filter(
                appointment=appointment,
                service_provider=request.user.service_provider,
                status='pending'
            ).exists():
                return JsonResponse({'success': False, 'error': 'You already have a pending offer for this appointment.'}, status=400)

            if not is_servicer and Bargaining.objects.filter(
                appointment=appointment,
                offered_by='user',
                status='pending'
            ).exists():
                return JsonResponse({'success': False, 'error': 'You already have a pending offer for this appointment.'}, status=400)


            bargain = Bargaining.objects.create(
                appointment=appointment,
                service_provider=request.user.service_provider if is_servicer else None,
                initial_price=appointment.expected_amount,
                servicer_offer_price=data.get('servicer_offer') if is_servicer else None,
                user_offer_price=data.get('user_offer') if not is_servicer else None,
                message=data.get('message', ''),
                status='pending',
                offered_by='servicer' if is_servicer else 'user'
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
                # If there are any pending offers (from either user or other servicers),
                # the servicer should ideally go through the bargaining process
                # or explicitly reject existing offers if they want to accept the initial price directly.
                # For simplicity, we'll prevent direct acceptance if there are *any* pending offers.
                if Bargaining.objects.filter(appointment=appointment, status='pending').exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'There are pending offers for this appointment. Please use the bargaining feature.'
                    }, status=400)

                appointment.status = 'accepted'
                appointment.servicer_assigned = request.user.service_provider
                if appointment.servicer_assigned:
                    _calculate_and_save_distance(appointment, appointment.servicer_assigned)

                appointment.generate_otp()
                appointment.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Appointment accepted at the initial expected amount.',
                    'otp': appointment.otp,
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