from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone=phone,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, phone, password=None):
        user = self.create_user(
            username=username,
            email=email,
            phone=phone,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10, unique=True)
    
    objects = CustomUserManager()
    
    REQUIRED_FIELDS = ['email', 'phone']


from django.db import models
from django.conf import settings
from doctor.models import Doctor, Slot  # Assuming Doctor and Slot models exist
from django.utils.timezone import now

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=now)  # ✅ New field
    time = models.TimeField(default="00:00:00")

    def __str__(self):
        return f"{self.user.username} booked {self.doctor.user.username} at {self.slot.start_time}"


