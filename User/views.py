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
    if request.method == 'GET':
        data = json.loads(request.body)
        email = data['email']
        if CustomUser.objects.filter(email=email).exists and request.user.is_authenticated and request.user.is_active:
            user = CustomUser.objects.get(email=email)
            print()
            response = {
                'status': 'success',
                'email': user.email,
                'username': user.username,
                'avatar_url': user.avatar_url,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'is_creator': user.is_creator,
                'follower_id_list': list(user.follower_id_list.values()),
                'following_id_list': list(user.following_id_list.values())
            }
            return JsonResponse({'status': 'success', 'data': response})
        else:
            if not CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'error': 'User does not exist'})
            elif not request.user.is_authenticated:
                return JsonResponse({'error': 'user has not been authenticated'})
            else:
                return JsonResponse({'error': 'user has been banned'})
    else:
        return JsonResponse({'error': 'method not allowed'})
