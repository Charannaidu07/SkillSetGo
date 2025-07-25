# yourapp/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
#from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.conf import settings

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('user', 'Regular User'),
        ('servicer', 'Servicer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')


class Book_Appointment(models.Model):
    ISSUE_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('cleaning', 'Cleaning'),
        ('teaching', 'Teaching'),
        ('technical', 'Technical Support'),
        ('medical', 'Medical'),
        ('electrical', 'Electrical'),
        ('carpentry', 'Carpentry'),
        ('others', 'Others'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15)
    issue = models.CharField(max_length=20, choices=ISSUE_CHOICES)
    custom_issue = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Location Fields
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, default="India", null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Image Fields
    image1 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image2 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Appointment by {self.user.username} for {self.get_issue_display()}"
    
    def get_issue_domain(self):
        return self.custom_issue if self.issue == 'others' else self.get_issue_display()
    
    def get_full_location(self):
        return f"{self.address}, {self.city}, {self.state}, {self.pincode}, {self.country}"


class ServiceProviderDetails(models.Model):
    """
    Model to store service provider's personal and professional details
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_provider'
    )
    full_name = models.CharField(max_length=100)
    profile_photo = models.ImageField(
        upload_to='service_providers/profile_photos/',
        blank=True,
        null=True
    )
    mobile_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)]
    )
    whatsapp_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)],
        blank=True,
        null=True
    )
    alternate_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)],
        blank=True,
        null=True
    )
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    aadhar_number = models.CharField(
        max_length=12,
        validators=[MinLengthValidator(12), MaxLengthValidator(12)],
        unique=True
    )
    service_provider_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False  # Will be auto-generated
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} (ID: {self.service_provider_id})"

    def save(self, *args, **kwargs):
        if not self.service_provider_id:
        # Get the last service provider ID
            last_provider = ServiceProviderDetails.objects.order_by('-service_provider_id').first()
        
            if last_provider and last_provider.service_provider_id:
            # Extract the numeric part, increment by 1
                last_number = int(last_provider.service_provider_id[2:])
                new_number = last_number + 1
            else:
            # If no providers exist yet, start from 11111111
                new_number = 11111111
            
        # Format as SP followed by 8 digits
            self.service_provider_id = f"SP{new_number:08d}"
    
        super().save(*args, **kwargs)

    def get_full_address(self):
        return f"{self.address}, {self.city}, {self.state} - {self.pincode}"


class ServiceProviderBankDetails(models.Model):
    """
    Model to store service provider's banking and payment details
    """
    service_provider = models.OneToOneField(
        ServiceProviderDetails,
        on_delete=models.CASCADE,
        related_name='bank_details'
    )
    pan_number = models.CharField(
        max_length=10,
        validators=[MinLengthValidator(10), MaxLengthValidator(10)],
        unique=True
    )
    bank_account_number = models.CharField(
        max_length=18,
        validators=[MinLengthValidator(9), MaxLengthValidator(18)]
    )
    bank_name = models.CharField(max_length=100)
    ifsc_code = models.CharField(
        max_length=11,
        validators=[MinLengthValidator(11), MaxLengthValidator(11)]
    )
    upi_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    upi_mobile_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)],
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bank details for {self.service_provider.full_name}"

    def get_bank_info(self):
        return (
            f"Bank: {self.bank_name}\n"
            f"Account: {self.bank_account_number}\n"
            f"IFSC: {self.ifsc_code}"
        )
    
