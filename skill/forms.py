# yourapp/forms.py
from allauth.account.forms import SignupForm
from django import forms

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