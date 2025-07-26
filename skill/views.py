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
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from io import BytesIO
import os
from django.conf import settings
from reportlab.lib.utils import ImageReader


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
