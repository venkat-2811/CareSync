from django.db import models
from django.conf import settings  # Import settings to get AUTH_USER_MODEL

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    phone_number = models.CharField(max_length=10, unique=True)
    hospital_name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField()
    available_days = models.CharField(max_length=100)  # Example: "Monday, Wednesday, Friday"
    profile_picture = models.ImageField(upload_to="doctor_profiles/", blank=True, null=True)
    id_proof = models.FileField(upload_to="doctor_id_proofs/")
    is_approved = models.BooleanField(default=False)  # Admin can approve doctors

    def __str__(self):
        return f"Dr. {self.user.username} ({self.specialization})"

    @property
    def email(self):
        return self.user.email  # Access email from the user model

from django.db import models
from django.conf import settings
from datetime import timedelta

class Slot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('closed', 'Closed'),
    ]

    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    booked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="booked_slots")
    
    def __str__(self):
        return f"{self.doctor.username} | {self.start_time} - {self.end_time} | {self.status}"


