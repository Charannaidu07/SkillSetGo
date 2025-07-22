# yourapp/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
#from django.contrib.auth.models import User
from django.conf import settings
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('user', 'Regular User'),
        ('servicer', 'Servicer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')

#class Book_Appointment(models):
    #userid-forign key
    #contact number
    #4 images
    #issue(plumbing,cleaning,teaching,technical,medical,.............,others)
        #if issue==others-text(enter issue domain)
    #desc
    #expected amount to be paid to servicer
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
    image1 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image2 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='appointment_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Appointment by {self.user.username} for {self.get_issue_display()}"
    
    def get_issue_domain(self):
        return self.custom_issue if self.issue == 'others' else self.get_issue_display()