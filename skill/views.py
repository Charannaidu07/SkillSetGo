from django.shortcuts import render,redirect
from django.contrib.auth.models import auth
from .models import CustomUser,Book_Appointment
from django.contrib.auth.decorators import login_required
from .forms import BookAppointmentForm
from .forms import ServiceProviderForm, ServiceProviderBankForm,ServiceInitialRegistrationPaymentForm
from .models import ServiceProviderDetails, ServiceProviderBankDetails ,ServiceInitialRegistrationPayment,Book_Appointment
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import auth
from django.views.decorators.http import require_GET
from django.http import JsonResponse

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        user = request.user
        context = {
            'user': user,
            'user_type_display': user.get_user_type_display()  # Gets the display value
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
        'user_type_display': user.get_user_type_display()  # Gets the display value
    }
    return render(request,'profile.html',context)

@login_required
def service_provider_register(request):
    # Check if already registered
    if hasattr(request.user, 'service_provider'):
        return redirect('service_provider_dashboard')
    
    if request.method == 'POST':
        form = ServiceProviderForm(request.POST, request.FILES)
        bank_form = ServiceProviderBankForm(request.POST)
        payment_form = ServiceInitialRegistrationPaymentForm(request.POST, request.FILES)  # Note: Added request.FILES for payment proof
        # Manual validation for checkboxes
        accept_terms = request.POST.get('accept_terms') == 'on'
        accept_payment_terms = request.POST.get('accept_payment_terms') == 'on'
        
        if not accept_terms or not accept_payment_terms:
            messages.error(request, "You must accept all terms and conditions")
            return render(request, 'serviceproviderregister.html', {
                'form': form,
                'bank_form': bank_form,
                'payment_form': payment_form,
            })
        if form.is_valid() and bank_form.is_valid() and payment_form.is_valid():
            # Save service provider details
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            
            # Save bank details
            bank_details = bank_form.save(commit=False)
            bank_details.service_provider = provider
            bank_details.save()

            # Save payment details
            payment_details = payment_form.save(commit=False)
            payment_details.user = request.user
            payment_details.service_provider = provider
            payment_details.save()
            
            messages.success(request, 'Registration successful! Your account is under verification.')
            return redirect('service_provider_dashboard')
    else:
        form = ServiceProviderForm()
        bank_form = ServiceProviderBankForm()
        payment_form = ServiceInitialRegistrationPaymentForm()  # Consistent naming

    return render(request, 'serviceproviderregister.html', {
        'form': form,
        'other_preference1': request.POST.get('other_preference1', ''),
        'other_preference2': request.POST.get('other_preference2', ''),
        'bank_form': bank_form,
        'payment_form': payment_form  # Consistent naming
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

def appointments(request):
    provider = request.user.service_provider
    appoint=Book_Appointment.objects.order_by('-created_at')
    context = {
        'provider': provider,
        'appointments':appoint,
    }
    return render(request,'appointments.html',context)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import Bargaining
import json
@method_decorator(csrf_exempt, name='dispatch')
class BargainView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            appointment = Book_Appointment.objects.get(id=data['appointment_id'])
            
            # Create or update bargaining entry
            bargain, created = Bargaining.objects.update_or_create(
                appointment=appointment,
                service_provider=request.user.service_provider,
                defaults={
                    'servicer_offer_price': data.get('servicer_offer'),
                    'user_offer_price': data.get('user_offer'),
                    'message': data.get('message', ''),
                    'status': 'pending'
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Offer submitted successfully',
                'bargain_id': bargain.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AcceptBargainView(View):
    def post(self, request, bargain_id):
        try:
            bargain = Bargaining.objects.get(id=bargain_id)
            if request.user == bargain.appointment.user:
                # User accepting servicer's offer
                bargain.status = 'accepted'
                bargain.final_price = bargain.servicer_offer_price
                bargain.save()
                
                # Update appointment with final price
                bargain.appointment.expected_amount = bargain.final_price
                bargain.appointment.save()
                
                return JsonResponse({'success': True, 'message': 'Offer accepted successfully'})
            else:
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AcceptAppointmentView(View):
    def post(self, request, appointment_id):
        try:
            appointment = Book_Appointment.objects.get(id=appointment_id)
            accepted_bargain = appointment.bargains.filter(status='accepted').first()
            
            if not accepted_bargain:
                return JsonResponse({
                    'success': False,
                    'error': 'No accepted negotiation found'
                }, status=400)
                
            appointment.status = 'accepted'
            appointment.expected_amount = accepted_bargain.final_price
            appointment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Appointment accepted successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
@require_GET
def appointment_details(request, appointment_id):
    try:
        appointment = Book_Appointment.objects.get(id=appointment_id)
        
        # Get bargaining history
        bargaining_history = []
        for bargain in Bargaining.objects.filter(appointment=appointment).order_by('-created_at'):
            bargaining_history.append({
                'id': bargain.id,
                'offer_price': str(bargain.servicer_offer_price),
                'initial_price': str(bargain.initial_price),
                'message': bargain.message,
                'status': bargain.status,
                'status_display': bargain.get_status_display(),
                'offered_by': 'servicer' if bargain.service_provider.user == request.user else 'user',
                'created_at': bargain.created_at.isoformat(),
                'updated_at': bargain.updated_at.isoformat()
            })
        
        # Prepare image URLs
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
            'expected_amount': str(appointment.expected_amount),
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
            'status': appointment.status
        }
        return JsonResponse(data)
    except Book_Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)