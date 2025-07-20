from django.urls import path
from . import views
urlpatterns=[
    path('',views.index,name='index'),
    path('logout',views.logout,name='logout'),
    path('profile',views.profile,name='profile'),
    path('service',views.service,name='service'),
]
