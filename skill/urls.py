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
]
