from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('profile/', views.profile, name='profile'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('doctor-slots/<int:doctor_id>/', views.view_doctor_slots, name='view_doctor_slots'),
    path("book-slot/<int:slot_id>/", views.create_razorpay_order, name="book_slot"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("bookings/", views.booking_details, name="booking_details"),
]
