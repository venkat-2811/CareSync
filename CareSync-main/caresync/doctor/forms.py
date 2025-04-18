from django import forms
from .models import Doctor, Slot
from django.contrib.auth import get_user_model

User = get_user_model() 

class DoctorRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Doctor
        fields = ['phone_number', 'hospital_name', 'specialization', 'experience_years', 'available_days', 'profile_picture', 'id_proof']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        phone_number = self.cleaned_data.get("phone_number")
        
        # Check if phone number already exists
        if User.objects.filter(phone=phone_number).exists():
            raise forms.ValidationError("A user with this phone number already exists.")

        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            phone=phone_number,
            password=self.cleaned_data["password"]
        )
    
        doctor = super().save(commit=False)
        doctor.user = user
        if commit:  
            doctor.save()
        return doctor

#slots form
class SlotForm(forms.ModelForm):
    class Meta:
        model = Slot
        fields = ['start_time', 'end_time', 'status']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'status': forms.Select(choices=Slot.STATUS_CHOICES),
        }