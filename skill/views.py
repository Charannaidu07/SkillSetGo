from django.shortcuts import render,redirect
from django.contrib.auth.models import auth
from .models import CustomUser,Book_Appointment
from django.contrib.auth.decorators import login_required
from .forms import BookAppointmentForm
from .forms import ServiceProviderForm, ServiceProviderBankForm
from .models import ServiceProviderDetails, ServiceProviderBankDetails
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import auth


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
        
        if form.is_valid() and bank_form.is_valid():
            # Save service provider details
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            
            # Save bank details
            bank_details = bank_form.save(commit=False)
            bank_details.service_provider = provider
            bank_details.save()
            
            messages.success(request, 'Registration successful! Your account is under verification.')
            return redirect('service_provider_dashboard')
    else:
        form = ServiceProviderForm()
        bank_form = ServiceProviderBankForm()

    return render(request, 'serviceproviderregister.html', {
        'form': form,
        'bank_form': bank_form
    })

@login_required
def service_provider_dashboard(request):
    if not hasattr(request.user, 'service_provider'):
        return redirect('service_provider_register')
    
    provider = request.user.service_provider
    return render(request, 'serviceproviderdashboard.html', {
        'provider': provider
    })