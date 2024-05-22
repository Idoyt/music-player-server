"""
URL configuration for Server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from User.views import (
    login_view,
    logout_view,
    check_email_view,
    check_login,
    check_is_staff,

    new_user_info,
    get_user_info,
    update_user_info,
    delete_user_info,

    get_task,
    update_task,
    delete_task,

    new_music_info,
    new_music_info_by_admin,
    update_music_info,
    delete_music_info,
    get_music_info,

    new_playlist_info,
    delete_playlist_info,
    update_playlist_info,
    get_playlist_info,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('check_email/', check_email_view, name='check_email'),
    path('check_login/', check_login, name='check_login'),
    path('check_is_staff/', check_is_staff, name='check_is_staff'),

    path('new_user_info/', new_user_info, name='new_user_info'),
    path('get_user_info/', get_user_info, name='get_user_info'),
    path('update_user_info/', update_user_info, name='update_user_info'),
    path('delete_user_info/', delete_user_info, name='delete_user_info'),

    path('get_task/', get_task, name='get_task'),
    path('update_task/', update_task, name='update_task'),
    path('delete_task/', delete_task, name='delete_task'),

    path('new_music_info/', new_music_info, name='new_music_info'),
    path('new_music_info_by_admin/', new_music_info_by_admin, name='new_music_info_by_admin'),
    path('update_music_info/', update_music_info, name='update_music_info'),
    path('delete_music_info/', delete_music_info, name='delete_music_info'),
    path('get_music_info/', get_music_info, name='get_music_info'),

    path('new_playlist_info/', new_playlist_info, name='new_playlist_info'),
    path('update_playlist_info/', update_playlist_info, name='update_playlist_info'),
    path('delete_playlist_info/', delete_playlist_info, name='delete_playlist_info'),
    path('get_playlist_info/', get_playlist_info, name='get_playlist_info'),
]
