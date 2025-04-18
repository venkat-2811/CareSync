from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegistrationForm, LoginForm, ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
from .models import CustomUser
from django.core.mail import send_mail
from django.conf import settings
import random
from django.utils import timezone
from reports.models import ReportFolder
from django.shortcuts import render
from doctor.models import Doctor, Slot
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                
                # Generate OTP and store in session
                otp = generate_otp()
                request.session['reset_otp'] = otp
                request.session['reset_email'] = email
                request.session['reset_timestamp'] = timezone.now().timestamp()
                
                # Send OTP via email
                send_mail(
                    'Password Reset OTP',
                    f'Your OTP for password reset is: {otp}\nThis OTP is valid for 10 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, 'OTP has been sent to your email.')
                return redirect('verify_otp')
            except Exception as e:
                messages.error(request, 'Error sending OTP. Please try again.')
    else:
        form = ForgotPasswordForm()
    return render(request, 'forgot_password.html', {'form': form})

def verify_otp(request):
    if 'reset_otp' not in request.session:
        messages.error(request, 'Please request OTP first')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data.get('otp')
            stored_otp = request.session.get('reset_otp')
            timestamp = request.session.get('reset_timestamp')
            
            # Check if OTP is expired (10 minutes)
            current_time = timezone.now().timestamp()
            if current_time - timestamp > 600:
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('forgot_password')
            
            if otp == stored_otp:
                # Clear OTP from session
                del request.session['reset_otp']
                del request.session['reset_timestamp']
                messages.success(request, 'OTP verified successfully')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid OTP')
    else:
        form = OTPVerificationForm()
    return render(request, 'verify_otp.html', {'form': form})

def reset_password(request):
    if 'reset_email' not in request.session:
        messages.error(request, 'Invalid password reset request')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                email = request.session.get('reset_email')
                user = CustomUser.objects.get(email=email)
                user.set_password(form.cleaned_data.get('password1'))
                user.save()
                
                # Clear session data
                del request.session['reset_email']
                
                messages.success(request, 'Password has been reset successfully. Please login with your new password.')
                return redirect('login')
            except Exception as e:
                messages.error(request, 'Error resetting password. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResetPasswordForm()
    return render(request, 'reset_password.html', {'form': form})

@login_required
def profile(request):
    folders = ReportFolder.objects.filter(user=request.user)
    context = {
        'user': request.user,
        'folders' : folders,
    }
    return render(request, 'profile.html', context)

#booking and slots
from django.shortcuts import render, get_object_or_404, redirect
from doctor.models import Doctor, Slot
from django.contrib.auth.decorators import login_required

@login_required
def book_appointment(request):
    query = request.GET.get('q', '')  # Get search query from GET request
    doctors = []

    if query:
        doctors = Doctor.objects.filter(specialization__icontains=query)  # Search for doctors
    
    return render(request, 'book_appointment.html', {'doctors': doctors, 'query': query})


@login_required
def view_doctor_slots(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    slots = Slot.objects.filter(doctor=doctor.user, status='available')  # Fetch available slots
    
    return render(request, 'doctor_slots.html', {'doctor': doctor, 'slots': slots})


import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from doctor.models import Slot
from .models import Booking
from doctor.models import Doctor

@login_required
def create_razorpay_order(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id, status="available")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    amount = 50000  # Example: Rs. 500 (in paise)
    order_data = {
        "amount": amount,  
        "currency": "INR",
        "payment_capture": "1"
    }
    order = client.order.create(data=order_data)

    context = {
        "slot": slot,
        "amount": amount / 100,  # Convert to rupees
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": order["id"],
    }
    return render(request, "payment.html", context)



import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Booking, Slot
from doctor.models import Doctor

@login_required
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    slot_id = request.GET.get('slot_id')

    if not payment_id or not slot_id:
        messages.error(request, "Invalid payment or slot details.")
        return redirect('payment_failed')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        payment_details = client.payment.fetch(payment_id)

        if payment_details["status"] == "captured":  # ✅ Payment was successful
            slot = get_object_or_404(Slot, id=slot_id)

            if slot.status != "available":  
                messages.error(request, "This slot is already booked.")
                return redirect('booking_details')

            doctor = get_object_or_404(Doctor, user=slot.doctor)
            amount = 500  # Example fee

            # ✅ Create Booking & Assign Patient to Slot
            booking = Booking.objects.create(
                user=request.user,
                doctor=doctor,
                slot=slot,  # Link slot to patient
                amount=amount,
                payment_id=payment_id,
                date=slot.start_time.date(),
                time=slot.start_time.time()
            )

            # ✅ Mark Slot as Booked
            slot.status = 'booked'
            slot.save()

            messages.success(request, "Appointment booked successfully! Your slot is confirmed.")
            return redirect('booking_details')

        else:
            messages.error(request, "Payment failed. Please try again.")
            return redirect('payment_failed')

    except razorpay.errors.BadRequestError:
        messages.error(request, "Payment verification failed.")
        return redirect('payment_failed')


@login_required
def booking_details(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, "bookings.html", {"bookings": bookings})


