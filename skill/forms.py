from allauth.account.forms import SignupForm
from django import forms
from .models import Book_Appointment, ServiceProviderBankDetails, ServiceProviderDetails, ServiceInitialRegistrationPayment
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone

class CustomSignupForm(SignupForm):
    user_type = forms.ChoiceField(
        label="Are you a User or Servicer?",
        choices=(('user', 'User'), ('servicer', 'Servicer')),
        widget=forms.RadioSelect,
    )

    def save(self, request):
        user = super().save(request)
        user.user_type = self.cleaned_data['user_type']
        user.save()
        return user

class BookAppointmentForm(forms.ModelForm):
    class Meta:
        model = Book_Appointment
        fields = [
            'contact_number', 'full_name','issue', 'custom_issue', 'description', 
            'expected_amount', 'address', 'city', 'state', 'country', 
            'pincode', 'expected_time', 'image1', 'image2', 'image3', 'image4'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control shadow-sm',
                'placeholder': 'Describe your service requirement in detail'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control shadow-sm',
                'placeholder': 'Full street address'
            }),
            'expected_time': forms.DateTimeInput(attrs={
                'class': 'form-control flatpickr-datetime',
                'data-enable-time': 'true',
                'data-date-format': 'm/d/Y h:i K',
                'data-time_24hr': 'false',
                'data-min-date': 'today'
            }),
            
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control shadow-sm',
                'placeholder': 'e.g. +91 9876543210'
            }),
            'expected_amount': forms.NumberInput(attrs={
                'class': 'form-control shadow-sm',
                'placeholder': 'Estimated amount in ₹',
                'min': '0',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control shadow-sm',
                'value': 'India'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expected_time'].input_formats = ['%m/%d/%Y %I:%M %p', '%Y-%m-%d %H:%M:%S']
        # Common attributes for all fields
        for field in self.fields:
            if field not in self.Meta.widgets:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control shadow-sm'
                })
            
            if field.startswith('image'):
                self.fields[field].required = False
                self.fields[field].widget.attrs.update({
                    'class': 'form-control d-none image-upload-input'
                })
        
        # Set default country to India
        self.fields['country'].initial = 'India'
        
    def clean(self):
        cleaned_data = super().clean()
        issue = cleaned_data.get('issue')
        custom_issue = cleaned_data.get('custom_issue')
        expected_time = cleaned_data.get('expected_time')
        
        if issue == 'others' and not custom_issue:
            self.add_error('custom_issue', "Please specify the issue when selecting 'Others'.")
            
        # Validate location fields
        address = cleaned_data.get('address')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        pincode = cleaned_data.get('pincode')
        
        if not all([address, city, state, pincode]):
            # This general error might be less specific, consider adding errors to individual fields
            raise forms.ValidationError("Please provide complete address details.")
            
        return cleaned_data

    def clean_expected_time(self):
        expected_time = self.cleaned_data.get('expected_time')
        if expected_time and expected_time < timezone.now():
            raise forms.ValidationError("Service date/time must be in the future.")
        return expected_time

class ServiceProviderForm(forms.ModelForm):
    mobile_number = forms.CharField(
        validators=[MinLengthValidator(10)],
        widget=forms.TextInput(attrs={'pattern': '[0-9]{10,}', 'title': '10 digit mobile number'})
    )
    
    # Custom form fields (not in model)
    other_preference1 = forms.CharField(
        required=False,
        label="Specify Service 1",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your custom service'
        })
    )
    
    other_preference2 = forms.CharField(
        required=False,
        label="Specify Service 2",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your custom service'
        })
    )

    class Meta:
        model = ServiceProviderDetails
        fields = [
            'full_name', 'profile_photo', 'mobile_number',
            'whatsapp_number', 'alternate_number', 'address',
            'city', 'state', 'pincode', 'aadhar_number',
            'Preference1', 'Preference2','other_preference1','other_preference2'  # Model fields only
        ]
        widgets = {
            'Preference1': forms.Select(attrs={
                'class': 'form-control preference-select',
                'data-other-field': 'other_preference1'
            }),
            'Preference2': forms.Select(attrs={
                'class': 'form-control preference-select',
                'data-other-field': 'other_preference2'
            }),
            'aadhar_number': forms.TextInput(attrs={
                'pattern': '[0-9]{12}',
                'title': '12 digit Aadhar number'
            }),
            'pincode': forms.TextInput(attrs={
                'pattern': '[0-9]{6}',
                'title': '6 digit pincode'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'file-upload-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize choices from model
        self.fields['Preference1'].choices = self.instance.PREFERENCE_CHOICES
        self.fields['Preference2'].choices = self.instance.PREFERENCE_CHOICES

    def clean(self):
        cleaned_data = super().clean()
        # Handle Preference1
        Preference1 = cleaned_data.get('Preference1')
        other_preference1 = cleaned_data.get('other_preference1')
        Preference2 = cleaned_data.get('Preference2')
        other_preference2 = cleaned_data.get('other_preference2')
        if Preference1 == 'others' and not other_preference1:
            raise forms.ValidationError("Please specify the issue when selecting 'Others'.")
        if Preference2 == 'others' and not other_preference2:
            raise forms.ValidationError("Please specify the issue when selecting 'Others'.")
        return cleaned_data

class ServiceProviderBankForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderBankDetails
        fields = [
            'pan_number', 'bank_account_number', 
            'bank_name', 'ifsc_code', 'upi_id', 'upi_mobile_number'
        ]
        widgets = {
            'pan_number': forms.TextInput(attrs={
                'pattern': '[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}',
                'title': 'PAN format: ABCDE1234F'
            }),
            'ifsc_code': forms.TextInput(attrs={
                'pattern': '[A-Za-z]{4}0[A-Za-z0-9]{6}',
                'title': 'IFSC format: ABCD0123456'
            }),
        }

class ServiceInitialRegistrationPaymentForm(forms.ModelForm):
    class Meta:
        model = ServiceInitialRegistrationPayment
        fields = ['amount_paid', 'payment_proof']
        widgets = {
            'payment_proof': forms.FileInput(attrs={
                'class': 'file-upload-input'
            }),
        }