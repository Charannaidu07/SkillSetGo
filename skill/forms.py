# yourapp/forms.py
from allauth.account.forms import SignupForm
from django import forms
from .models import Book_Appointment,ServiceProviderBankDetails,ServiceProviderDetails
from django.core.validators import MinLengthValidator, MaxLengthValidator

class CustomSignupForm(SignupForm):
    user_type = forms.ChoiceField(
        label="Are you a User or Servicer?",
        choices=(('user', 'User'), ('servicer', 'Servicer')),
        widget=forms.RadioSelect,
    )

    def save(self, request):
        user = super().save(request)  # Parent class creates user
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
    
    class Meta:
        model = ServiceProviderDetails
        fields = [
            'full_name', 'profile_photo', 'mobile_number', 
            'whatsapp_number', 'alternate_number', 'address',
            'city', 'state', 'pincode', 'aadhar_number'
        ]
        widgets = {
            'aadhar_number': forms.TextInput(attrs={'pattern': '[0-9]{12}', 'title': '12 digit Aadhar number'}),
            'pincode': forms.TextInput(attrs={'pattern': '[0-9]{6}', 'title': '6 digit pincode'}),
        }

class ServiceProviderBankForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderBankDetails
        fields = [
            'pan_number', 'bank_account_number', 
            'bank_name', 'ifsc_code', 'upi_id', 'upi_mobile_number'
        ]
        widgets = {
            'pan_number': forms.TextInput(attrs={'pattern': '[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}', 'title': 'PAN format: ABCDE1234F'}),
            'ifsc_code': forms.TextInput(attrs={'pattern': '[A-Za-z]{4}0[A-Za-z0-9]{6}', 'title': 'IFSC format: ABCD0123456'}),
        }