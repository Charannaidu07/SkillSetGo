from django.urls import path
from . import views
from . import gid
urlpatterns=[
    path('',views.index,name='index'),
    path('logout',views.logout,name='logout'),
    path('profile',views.profile,name='profile'),
    path('service',views.service,name='service'),
    path('book_appointment',views.book_appointment,name='book_appointment'),
    path('appointment_success',views.appointment_success,name='appointment_success'),
    path('register/', views.service_provider_register, name='service_provider_register'),
    path('dashboard/', views.service_provider_dashboard, name='service_provider_dashboard'),
    path('generate_id_card/', gid.generate_id_card, name='generate_id_card'),
    path('appointments/', views.appointments, name='appointments'),
    path('bookmarked_appointments/', views.bookmarked_appointments, name='bookmarked_appointments'),  # New URL for bookmarked appointments
    path('my_work/', views.my_work, name='my_work'),  # New URL for accepted work
    path('api/appointments/<int:appointment_id>/', views.appointment_details, name='appointment-details'),
    path('api/bargain/', views.BargainView.as_view(), name='bargain'),
    path('api/bargain/<int:bargain_id>/accept/', views.AcceptOfferView.as_view(), name='accept_offer'), # Handles both user/servicer accepting an offer
    path('api/bargain/<int:bargain_id>/reject/', views.RejectOfferView.as_view(), name='reject_offer'), # Handles both user/servicer rejecting an offer
    path('api/appointments/<int:appointment_id>/accept/', views.AcceptAppointmentView.as_view(), name='accept_appointment'), # For servicer to accept initial price
    path('api/appointments/<int:appointment_id>/confirm/', views.ConfirmAppointmentView.as_view(), name='confirm_appointment'), # For user to confirm final price
    path('api/appointments/<int:appointment_id>/verify-otp/', views.VerifyOtpView.as_view(), name='verify_otp'), # NEW URL
    path('api/appointments/<int:appointment_id>/rate-servicer/', views.RateServicerView.as_view(), name='rate_servicer'), # NEW URL for rating
    path('api/appointments/<int:appointment_id>/bookmark/', views.BookmarkAppointmentView.as_view(), name='bookmark_appointment'), # New API for bookmarking
]