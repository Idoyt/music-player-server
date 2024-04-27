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
    new_user_info,
    login_view,
    logout_view,
    check_email_view,
    get_user_info,
    update_user_info,
    update_music_info
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', new_user_info, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('check_email/', check_email_view, name='check_email'),
    path('get_user_info/', get_user_info, name='get_user_info'),
    path('update_user_info/', update_user_info, name='update_user_info'),
    path('update_music_info/', update_music_info, name='update_music_info')

]
