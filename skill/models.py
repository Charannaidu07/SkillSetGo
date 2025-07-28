# yourapp/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.conf import settings
from django.db import transaction
from datetime import datetime
from django.utils import timezone
import random
import string

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('user', 'Regular User'),
        ('servicer', 'Servicer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')

class ServiceProviderDetails(models.Model):
    """
    Model to store service provider's personal and professional details
    """
    PREFERENCE_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('cleaning', 'Cleaning'),
        ('teaching', 'Teaching'),
        ('technical', 'Technical Support'),
        ('medical', 'Medical'),
        ('electrical', 'Electrical'),
        ('carpentry', 'Carpentry'),
        ('others', 'Others'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_provider'
    )
    full_name = models.CharField(max_length=100)
    profile_photo = models.ImageField(
        upload_to='service_providers/profile_photos/'
    )
    mobile_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)]
    )
    whatsapp_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)],
        null=False,
        blank=False,
    )
    alternate_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)],
        null=False,
        blank=False,
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
        editable=False
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    Preference1 = models.CharField(max_length=20, choices=PREFERENCE_CHOICES, null=False, blank=False)
    other_preference1 = models.CharField(max_length=50, blank=True, null=True)
    Preference2 = models.CharField(max_length=20, choices=PREFERENCE_CHOICES, null=True, blank=True)
    other_preference2 = models.CharField(max_length=50, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0) # Existing rating field
    total_ratings = models.IntegerField(default=0) # New field to sum all ratings
    num_ratings = models.IntegerField(default=0) # New field to count number of ratings

    def __str__(self):
        return f"{self.full_name} (ID: {self.service_provider_id})"

    def save(self, *args, **kwargs):
        if not self.service_provider_id:
            with transaction.atomic():
            # Get current year's last 2 digits
                year_suffix = datetime.now().strftime('%y')

            # Lock the table to prevent concurrent inserts
                last_provider = ServiceProviderDetails.objects.select_for_update()\
                    .filter(service_provider_id__startswith=f'SP{year_suffix}')\
                    .order_by('-service_provider_id').first()

                if last_provider and last_provider.service_provider_id:
                # Extract the 6-digit sequence part
                    last_sequence = int(last_provider.service_provider_id[4:])
                    new_sequence = last_sequence + 1
                else:
                # Start new sequence for the year
                    new_sequence = 111111

                self.service_provider_id = f"SP{year_suffix}{new_sequence:06d}"
                return super().save(*args, **kwargs)
        else:
            return super().save(*args, **kwargs)

    def get_full_address(self):
        return f"{self.address}, {self.city}, {self.state} - {self.pincode}"

    def update_rating(self, new_rating):
        self.total_ratings += new_rating
        self.num_ratings += 1
        if self.num_ratings > 0: # Avoid division by zero
            self.rating = self.total_ratings / self.num_ratings
        else:
            self.rating = 0.0
        self.save()


class Book_Appointment(models.Model):
    STATUS_CHOICES=[
        ('accepted','Accepted'),
        ('pending','Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
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
    full_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    issue = models.CharField(max_length=20, choices=ISSUE_CHOICES)
    custom_issue = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_id = models.CharField(max_length=15, unique=True, editable=False)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, default="India", null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    expected_time = models.DateTimeField(null=True, blank=True)
    image1 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image2 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    servicer_assigned = models.ForeignKey(
        ServiceProviderDetails,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_appointments'
    )
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0.0) # Field for calculated distance
    rating = models.PositiveIntegerField(null=True, blank=True,
                                        choices=[(i, str(i)) for i in range(1, 6)],
                                        verbose_name="Servicer Rating (1-5)") # New rating field

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment by {self.user.username} for {self.get_issue_display()}"

    def get_issue_domain(self):
        return self.custom_issue if self.issue == 'others' else self.get_issue_display()

    def get_full_location(self):
        return f"{self.address}, {self.city}, {self.state}, {self.pincode}, {self.country}"

    def generate_otp(self):
        self.otp = ''.join(random.choices(string.digits, k=6))
        # self.save() # Don't save here, save will be called by the view after setting other fields
        return self.otp

    def save(self, *args, **kwargs):
        if not self.booking_id:
            year_suffix = timezone.now().strftime('%y')
            with transaction.atomic():
                last_appointment = Book_Appointment.objects.select_for_update() \
                    .filter(booking_id__startswith=f'AB{year_suffix}') \
                    .order_by('-booking_id').first()

                if last_appointment:
                    last_seq = int(last_appointment.booking_id[4:])
                    new_seq = last_seq + 1
                else:
                    new_seq = 11111111111

                self.booking_id = f"AB{year_suffix}{new_seq:011d}"

        super().save(*args, **kwargs)


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
        null=False,
        blank=False,
    )
    upi_mobile_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(10)],
        null=False,
        blank=False,
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

class ServiceInitialRegistrationPayment(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_payments'
    )
    service_provider = models.ForeignKey(
        ServiceProviderDetails,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount_paid = models.PositiveIntegerField()
    payment_date = models.DateField(auto_now_add=True)
    payment_proof = models.ImageField(upload_to="payments/")
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of ₹{self.amount_paid} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Automatically set service_provider if not set
        if not self.service_provider_id and self.user_id:
            self.service_provider = ServiceProviderDetails.objects.get(user=self.user)
        super().save(*args, **kwargs)

class Bargaining(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'), # Both parties accepted
        ('rejected', 'Rejected'),
        ('user_accepted', 'User Accepted'), # User accepted servicer's offer
        ('servicer_accepted', 'Servicer Accepted'), # Servicer accepted user's offer
    ]

    appointment = models.ForeignKey(Book_Appointment, on_delete=models.CASCADE, related_name='bargains')
    service_provider = models.ForeignKey(ServiceProviderDetails, on_delete=models.CASCADE, null=True, blank=True)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2)
    servicer_offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    user_offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    offered_by = models.CharField(max_length=10, choices=[('user', 'User'), ('servicer', 'Servicer')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bargain for {self.appointment} - {self.get_status_display()}"

    def get_offer_price(self):
        if self.offered_by == 'user':
            return self.user_offer_price
        elif self.offered_by == 'servicer':
            return self.servicer_offer_price
        return None

class BargainingHistory(models.Model):
    bargaining = models.ForeignKey(
        Bargaining,
        on_delete=models.CASCADE,
        related_name='history'
    )
    offered_by = models.CharField(max_length=10, choices=[('user', 'User'), ('servicer', 'Servicer')])
    offered_price = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']