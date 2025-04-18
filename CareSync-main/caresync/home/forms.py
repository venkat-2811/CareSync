from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.core.exceptions import ValidationError

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=10, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError('Phone number must be 10 digits')
        if CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This phone number is already registered')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered. Please use a different email.')
        return email

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address')
        return email

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6, required=True)

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if not otp.isdigit():
            raise forms.ValidationError('OTP must contain only numbers')
        return otp

class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput,
        min_length=8,
        required=True
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput,
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')