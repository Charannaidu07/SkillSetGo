from allauth.account.forms import SignupForm
from django import forms
from .models import Book_Appointment, ServiceProviderBankDetails, ServiceProviderDetails, ServiceInitialRegistrationPayment
from django.core.validators import MinLengthValidator, MaxLengthValidator

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
        fields = ['contact_number', 'issue', 'custom_issue', 'description', 
                 'expected_amount', 'image1', 'image2', 'image3', 'image4']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image1'].required = False
        self.fields['image2'].required = False
        self.fields['image3'].required = False
        self.fields['image4'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        issue = cleaned_data.get('issue')
        custom_issue = cleaned_data.get('custom_issue')
        
        if issue == 'others' and not custom_issue:
            raise forms.ValidationError("Please specify the issue when selecting 'Others'.")
        
        return cleaned_data

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

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
        
    #     # Handle Preference1
    #     if self.cleaned_data.get('Preference1') == 'others':
    #         instance.Preference1 = self.cleaned_data.get('other_preference1', '').strip()
        
    #     # Handle Preference2
    #     if self.cleaned_data.get('Preference2') == 'others':
    #         instance.Preference2 = self.cleaned_data.get('other_preference2', '').strip()
        
    #     if commit:
    #         instance.save()
    #     return instance

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