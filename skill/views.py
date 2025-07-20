from django.shortcuts import render,redirect
from django.contrib.auth.models import auth
from .models import CustomUser
from django.contrib.auth.decorators import login_required
# Create your views here.
def index(request):
    return render(request, 'index.html')
def service(request):
    return render(request,'service.html')
def logout(request):
    auth.logout(request)
    return redirect('index')
@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
        'user_type_display': user.get_user_type_display()  # Gets the display value
    }
    return render(request,'profile.html',context)