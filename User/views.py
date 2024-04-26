import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser


# Create your views here.
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data['email']
        password = data['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'fail'})
    else:
        return JsonResponse({'status': 'fail'})


@csrf_exempt
def check_email_view(request):
    if request.method == 'POST':
        print(request.POST)
        data = json.loads(request.body)
        email = data['email']
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'fail', 'message': 'User does not exist'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'method not allowed'})


@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data['email']
        password = data['password']
        username = data['username']
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'email has been taken'})
        else:
            CustomUser.objects.create_user(email=email, password=password, username=username)
            return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'fail'})


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'fail'})


@csrf_exempt
def get_user_info(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data['email']
        if CustomUser.objects.filter(email=email).exists() and request.user.is_authenticated():
            selected_user = CustomUser.objects.get(email=email)
