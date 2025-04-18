from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import DoctorRegistrationForm
from .models import Doctor
from django.contrib.auth import get_user_model

User = get_user_model() 

# Doctor Registration View
def doctor_register(request):
    if request.method == "POST":
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("doctor_login")  # Redirect to login after successful registration
    else:
        form = DoctorRegistrationForm()
    
    return render(request, "dregister.html", {"form": form})

# Doctor Login View
def doctor_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and hasattr(user, "doctor"):  # Ensure user is a doctor
            login(request, user)
            return redirect("home")
        else:
            return render(request, "dlogin.html", {"error": "Invalid credentials or not a doctor."})

    return render(request, "dlogin.html")

# Doctor Logout
def doctor_logout(request):
    logout(request)
    return redirect("doctor_login")

# slots doctor 
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware
from datetime import datetime, timedelta, time
from .models import Slot
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime

@login_required
def generate_slots(request):
    if not hasattr(request.user, 'doctor'):
        return redirect('home')

    start_time = datetime.combine(datetime.today(), time(9, 0))  # 9 AM
    end_time = datetime.combine(datetime.today(), time(18, 0))  # 6 PM
    lunch_start = datetime.combine(datetime.today(), time(13, 0))  # 1 PM
    lunch_end = datetime.combine(datetime.today(), time(14, 0))  # 2 PM
    session_duration = timedelta(minutes=30)  # 30-minute session
    gap_duration = timedelta(minutes=10)  # 10-minute gap
    
    slots = []
    current_time = start_time
    while current_time < end_time:
        if lunch_start <= current_time < lunch_end:
            current_time = lunch_end  # Skip lunch break
        
        session_end = current_time + session_duration
        if session_end > lunch_start and current_time < lunch_start:
            current_time = lunch_end  # Skip to after lunch if needed
            continue
        
        slots.append({
            "start_time": make_aware(current_time),
            "end_time": make_aware(session_end),
        })
        
        current_time = session_end + gap_duration  # Add gap after session
    
    return render(request, 'create_slots.html', {'slots': slots})

@login_required
def save_slots(request):
    if request.method == "POST":
        selected_slots = request.POST.getlist("available_slots")

        if not selected_slots:
            print("No slots selected!")  # Debugging output

        for slot_id in selected_slots:
            print(f"Received slot data: {slot_id}")  # Debugging output

            try:
                start_time_str, end_time_str = slot_id.split("|")

                # Ensure datetime format is correct
                start_time = parse_datetime(start_time_str)
                end_time = parse_datetime(end_time_str)

                if not start_time or not end_time:
                    print(f"Skipping invalid datetime: {start_time_str}, {end_time_str}")
                    continue

                start_time = make_aware(start_time)
                end_time = make_aware(end_time)

                # Save slot
                Slot.objects.create(
                    doctor=request.user,
                    start_time=start_time,
                    end_time=end_time,
                    status='available'
                )
                print(f"Saved slot: {start_time} - {end_time}")

            except Exception as e:
                print(f"Error processing slot: {slot_id}, Error: {e}")

        return redirect('/doctor/view_slots/')

    return redirect('/doctor/create_slots/')


@login_required
def view_slots(request):
    if not hasattr(request.user, 'doctor'):
        return redirect('home')

    slots = Slot.objects.filter(doctor=request.user)
    return render(request, 'view_slots.html', {'slots': slots})


@login_required
def cancel_slot(request, slot_id):
    try:
        slot = Slot.objects.get(id=slot_id, doctor=request.user)
        slot.status = "closed"
        slot.save()
        print(f"Slot {slot_id} canceled successfully.")
    except Slot.DoesNotExist:
        print(f"Slot {slot_id} not found or unauthorized.")
    
    return redirect('/doctor/view_slots/')
import pytz
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from home.models import Booking
from django.utils.timezone import now, localtime

from datetime import datetime

@login_required
def view_appointments(request): 
    if not hasattr(request.user, 'doctor'):
        return redirect('home')

    doctor_instance = request.user.doctor  # ✅ Get the Doctor instance
    bookings = Booking.objects.filter(doctor=doctor_instance)  # ✅ Now it matches the ForeignKey

    current_datetime = localtime(now())  # Get current time in local timezone

    # Filters
    patient_name = request.GET.get('patient_name', '')
    date = request.GET.get('date', '')
    slot_time = request.GET.get('slot_time', '')

    if patient_name:
        bookings = bookings.filter(user__username__icontains=patient_name)

    if date:
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").date()
            bookings = bookings.filter(date=formatted_date)
        except ValueError:
            pass  # Ignore invalid date formats

    if slot_time:
        bookings = bookings.filter(time=slot_time)

    # Convert times to IST and check if slot is finished
    ist = pytz.timezone("Asia/Kolkata")
    for booking in bookings:
        # ✅ Combine `date` and `time` into a single datetime object
        booking_datetime = datetime.combine(booking.date, booking.time)

        # ✅ Assign UTC timezone first, then convert to IST
        booking_datetime = booking_datetime.replace(tzinfo=pytz.utc).astimezone(ist)

        # ✅ Store formatted time for the template
        booking.formatted_time = booking_datetime.strftime("%I:%M %p")  # Format as HH:MM AM/PM

        # ✅ Determine if the slot is finished
        booking.is_finished = booking_datetime < current_datetime

    return render(request, 'view_appointment.html', {
        'bookings': bookings,
        'current_datetime': current_datetime,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from reports.models import ReportFolder, Report
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def doctor_view_patient_folders(request, patient_id):
    # Check if the user is a doctor
    if not hasattr(request.user, 'doctor'):
        return redirect('home')
    
    # Get the patient
    patient = get_object_or_404(User, id=patient_id)
    
    # Check if this doctor has an appointment with this patient
    # This security check ensures doctors can only view folders of their patients
    doctor_instance = request.user.doctor
    has_appointment = Booking.objects.filter(
        doctor=doctor_instance, 
        user=patient
    ).exists()
    
    if not has_appointment:
        messages.error(request, "You don't have permission to view this patient's records.")
        return redirect('view_appointments')
    
    # Get all folders for this patient
    folders = ReportFolder.objects.filter(user=patient)
    
    return render(request, 'doctor_patient_folders.html', {
        'patient': patient,
        'folders': folders
    })


@login_required
def doctor_view_folder_reports(request, folder_id):
    # Check if the user is a doctor
    if not hasattr(request.user, 'doctor'):
        return redirect('home')
    
    # Get the folder
    folder = get_object_or_404(ReportFolder, id=folder_id)
    patient = folder.user
    
    # Security check: Verify doctor has appointment with this patient
    doctor_instance = request.user.doctor
    has_appointment = Booking.objects.filter(
        doctor=doctor_instance, 
        user=patient
    ).exists()
    
    if not has_appointment:
        messages.error(request, "You don't have permission to view these reports.")
        return redirect('view_appointments')
    
    # Get reports in this folder
    reports = Report.objects.filter(folder=folder)
    
    return render(request, 'doctor_folder_reports.html', {
        'folder': folder,
        'patient': patient,
        'reports': reports
    })

@login_required
def doctor_view_report_analysis(request, report_id):
    # Check if the user is a doctor
    if not hasattr(request.user, 'doctor'):
        return redirect('home')
    
    # Get the report
    report = get_object_or_404(Report, id=report_id)
    patient = report.user
    
    # Security check: Verify doctor has appointment with this patient
    doctor_instance = request.user.doctor
    has_appointment = Booking.objects.filter(
        doctor=doctor_instance, 
        user=patient
    ).exists()
    
    if not has_appointment:
        messages.error(request, "You don't have permission to view this analysis.")
        return redirect('view_appointments')
    
    return render(request, 'doctor_report_analysis.html', {
        'report': report,
        'patient': patient,
        'analysis_data': report.analysis_data
    })

