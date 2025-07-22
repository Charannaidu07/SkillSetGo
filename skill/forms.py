# yourapp/forms.py
from allauth.account.forms import SignupForm
from django import forms
from .models import Book_Appointment

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