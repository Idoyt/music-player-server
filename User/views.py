import json
import os
from datetime import datetime

from django.contrib.auth.hashers import check_password
import User.authorization_items as authorization_items
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Server import settings
from .models import CustomUser, MusicInfo, MusicPlayList, Comment, Task
import csv
from django.shortcuts import render


# 2024.4.28 记， 1. 记得将所有的delete、review操作添加 new task操作 2. 继续测试update_user_info接口
# 2024.4.29 记， 1. 在delete_task视图中添加删除task后的回滚操作

@csrf_exempt
# 接口已验证
def login_view(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method Not Allowed'})

    data = json.loads(request.body)
    email = data.get('email', None)
    password = data.get('password', None)
    user = authenticate(request, email=email, password=password)
    if email is None or password is None:
        return JsonResponse({'status': 'fail', 'message': 'Missing credentials'})
    # elif request.user.is_authenticated and email == request.user.email:
    #     logout(request)
    #     return JsonResponse({'status': 'fail', 'message': 'User already logged in, login again'})
    elif user is None:
        return JsonResponse({'status': 'fail', 'message': 'Email or Password is incorrect'})

    login(request, user)
    return JsonResponse({'status': 'success', 'message': 'Login'})


@csrf_exempt
# 接口已验证
def logout_view(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User does not login'})
    logout(request)
    return JsonResponse({'status': 'success', 'message': 'logged out'})


@csrf_exempt
# 接口已验证
def check_login(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})

    email = request.GET.get('email', None)

    if email is None:
        return JsonResponse({'status': 'fail', 'message': 'Missing parameters'})

    user = CustomUser.objects.get(email=email)
    if user.is_authenticated:
        return JsonResponse({'status': 'success', 'message': 'User logged in successfully'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'User does not exist or is not authenticated'})


@csrf_exempt
# 接口已验证
def check_email_view(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'method not allowed'})

    email = request.GET.get('email', None)
    if email is None:
        return JsonResponse({'status': 'fail', 'message': 'Email is required'})
    elif not CustomUser.objects.filter(email=email).exists():
        return JsonResponse({'status': 'fail', 'message': 'Email is not registered'})

    return JsonResponse({'status': 'success', 'message': 'email check successful'})


@csrf_exempt
def check_is_staff(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User does not exist or is not'})
    elif not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'User is not staff'})

    return JsonResponse({'status': 'success', 'message': 'check is staff successful'})


# 以下为各种增删改查函数

# 任务的增删改查
# data 所需格式为
# {'task_name': value, 'task_type': value, 'task_priority': value, 'task_tags': value, 'task_notes': value}
# 此方法已验证
def new_task(request, data):
    if not request.user.is_authenticated:
        return {'status': 'fail', 'message': 'User is not authenticated'}
    elif not data.get('task_type') in authorization_items.task_type:
        return {'status': 'fail', 'message': 'Task type not allowed'}

    to_save_data = {
        'task_name': data.get('task_name', 'Default Task'),
        'task_type': data.get('task_type', 'review.user'),
        'task_priority': data.get('task_priority', 0),
        'task_tags': data.get('task_tags', None),
        'task_creator': CustomUser.objects.get(email=request.user.email),
        'task_notes': data.get('task_notes', None),
        'task_state': 'to be done'
    }
    music_id = data.get('music_id', None)
    if music_id is not None:
        to_save_data['music_id'] = MusicInfo.objects.get(music_id=music_id)

    new_tasks = Task.objects.create(**to_save_data)
    new_tasks.save()
    return {'status': 'success', 'message': 'Task created successfully'}


@csrf_exempt
# 此接口已验证
def update_task(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User is not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'Only staff can update task'})

    data = json.loads(request.body.decode('utf-8'))
    task_id = data.get('task_id', None)
    # example: {'task_name': 'task name example', .....}
    update_item = dict(data.get('update_item', None))

    if task_id is None:
        return JsonResponse({'status': 'fail', 'message': 'Missing task_id'})
    elif update_item is None:
        return JsonResponse({'status': 'fail', 'message': 'Missing update_item'})
    elif not Task.objects.filter(task_id=task_id).exists():
        return JsonResponse({'status': 'fail', 'message': 'task not found'})
    elif not set(update_item.keys()).issubset(authorization_items.task_update_item):
        return JsonResponse({'status': 'fail', 'message': 'Item not allowed to change'})

    task_to_update = Task.objects.get(task_id=task_id)
    repeat = {}
    for key, value in update_item.items():
        if getattr(task_to_update, key) == value:
            repeat[key] = value
            continue
        setattr(task_to_update, key, value)
    task_to_update.save()

    if len(repeat) == len(update_item.keys()):
        return JsonResponse({'status': 'fail', 'message': 'All value to update repeat'})
    elif len(repeat) < len(update_item.keys()):
        return JsonResponse({
            'status': 'success',
            'message': {'description': 'Update success, but some values repeat as followed: ', 'value': repeat}
        })
    return JsonResponse({'status': 'success', 'message': 'Task updated successfully'})


@csrf_exempt
def delete_task(request):
    data = json.loads(request.body.decode('utf-8'))
    task_id_list = data.get('task_id_list', None)

    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User is not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'User is not staff users can delete'})
    elif len(task_id_list) == 0:
        return JsonResponse({'status': 'fail', 'message': 'Task list empty'})
    elif len(task_id_list) > 100:
        return JsonResponse({'status': 'fail', 'message': 'Task list to delete too long'})
    length = len(task_id_list)

    for task_id in task_id_list:
        task = Task.objects.get(id=task_id)
        if task is None:
            return {
                'status': 'fail',
                'message': 'task not found in index:' + task_id_list.index(task_id) + 'in task list'
            }
    for task_id in task_id_list:
        task = Task.objects.get(id=task_id)
        # 在这里添加rollback相关代码
        task.delete()
    message = 'Task'
    if length > 1:
        message = 'Tasks'
    return JsonResponse({'status': 'success', 'message': message + ' deleted successfully'})


@csrf_exempt
# 此接口已验证
def get_task(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User is authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'You are not authorized to get tasks list'})

    data = request.GET.get('data', {})

    data = dict(data)

    select_item = list(data.keys())

    if not set(select_item).issubset(set(authorization_items.task_item_to_get)):
        return JsonResponse({'status': 'fail', 'message': 'Invalid item for selecting tasks'})

    if None in data.values():
        return JsonResponse({'status': 'fail', 'message': 'Missing data for selecting tasks'})

    response = Task.objects.filter(**data).values()
    return JsonResponse({'status': 'success', 'message': list(response)})


# 用户信息的增删改查
@csrf_exempt
# 接口已验证
def new_user_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'method is not allowed'})
    data = json.loads(request.body)
    email = data.get('email', None)
    password = data.get('password', None)
    username = data.get('username', None)
    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse({'status': 'fail', 'message': 'email has been taken'})
    else:
        CustomUser.objects.create_user(email=email, password=password, username=username)
        return JsonResponse({'status': 'success', 'message': 'user registered successfully'})


@csrf_exempt
# 接口已验证
def update_user_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User not authenticated'})

    data = json.loads(request.body)
    data = dict(data.get('update_item', None))
    update_item = data.keys()

    email = request.user.email
    allowed_items = authorization_items.user_info_to_update_by_user
    if request.user.is_staff and 'email' in update_item:
        email = data['email']
        allowed_items = authorization_items.user_info_to_get_by_staff

    user_to_update = CustomUser.objects.get(email=email)

    if not set(update_item).issubset(set(allowed_items)):
        return JsonResponse({'status': 'fail', 'message': 'Update item not allowed'})
    elif None in update_item or None in data.values():
        return JsonResponse({'status': 'fail', 'message': 'Missing required fields'})

    for key, value in data.items():
        if key != 'password':
            setattr(user_to_update, key, value)
        else:
            if check_password(value, request.user.password):
                return JsonResponse({'status': 'fail', 'message': 'Repeated update'})
            user_to_update.set_password(value)
    user_to_update.save()
    return JsonResponse({'status': 'success', 'message': 'Updated successfully'})


# 策略： 普通用户可以提交删除本人账户的task，staff用户可以直接删除除了自己以外的所有用户
@csrf_exempt
# 接口已验证
def delete_user_info(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User not authenticated'})

    email = request.GET.get('email', None)
    if request.user.is_staff:
        if email is None:
            return JsonResponse({'status': 'fail', 'message': 'Missing email'})
        elif not CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'fail', 'message': 'User to delete does not exist'})

        user_to_delete = CustomUser.objects.get(email=email)

        if user_to_delete.email == request.user.email:
            return JsonResponse({'status': 'fail', 'message': 'You can not delete yourself'})

        user_to_delete.delete()
        return JsonResponse({'status': 'success', 'message': 'User successfully deleted'})
    else:
        email = request.user.email
        user_to_delete = CustomUser.objects.get(email=email)
        if user_to_delete.to_be_deleted:
            return JsonResponse({'status': 'fail', 'message': 'You have already submitted your delete task'})

        user_to_delete.to_be_deleted = True
        user_to_delete.save()

        task_response = new_task(request, {
            'task_name': 'Delete User',
            'task_type': 'delete.user',
            'task_priority': 0
        })
        if task_response['status'] == 'fail':
            return JsonResponse({'status': 'fail', 'message': task_response['message']})
        else:
            return JsonResponse({'status': 'success', 'message': 'delete request has been submitted'})


@csrf_exempt
# 接口已验证
def get_user_info(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'You are not authenticated'})

    if request.user.is_staff:
        quantity = request.GET.get('quantity', None)
        if quantity is None or not quantity.isdigit():
            return JsonResponse({'status': 'fail', 'message': 'Quantity must be a number'})
        if quantity == '0':
            all_user = CustomUser.objects.all().values(*authorization_items.user_info_to_get_by_staff)[:1000]
            response = list(all_user)
        else:
            email = request.GET.get('email', None)
            if email is None:
                email = request.user.email

            if not CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'status': 'fail', 'message': 'Email not found'})

            user = CustomUser.objects.filter(email=email).values(
                *authorization_items.user_info_to_get_by_staff
            )[:int(quantity)]

            response = list(user)
            if int(quantity) == 1:
                response = response[0]
        return JsonResponse({'status': 'success', 'message': response})

    else:
        if request.user.is_anonymous:
            return JsonResponse({'status': 'fail', 'message': 'User not found'})
        user = CustomUser.objects.get(email=request.user.email)
        if not user.is_active:
            return JsonResponse({'status': 'fail', 'message': 'You have been banned'})

        response = (CustomUser.objects.filter
        (email=request.user.email).values(*authorization_items.user_info_to_get_by_user)[0])
        return JsonResponse({'status': 'success', 'message': response})


# 增删改音频源文件
# 方法已验证
def new_file_source(file, music_id):
    extension = file.name.split('.')[-1]
    if extension not in authorization_items.allowed_upload_file_type:
        return {'status': 'fail', 'message': 'File extensions not allowed'}

    file_path = os.path.join(settings.MEDIA_URL, 'review/')
    if not os.path.exists(file_path + str(music_id)):
        os.mkdir(file_path + str(music_id))
    file_path = os.path.join(file_path, str(music_id))

    with open(file_path + '/' + file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return {'status': 'success', 'message': file_path}

    # file_name = str(music_id) + '.' + extension
    # if extension not in authorization_items.music_source_type:
    #     return {'status': 'fail', 'message': 'file extension not allowed'}
    #
    # file_path = os.path.join(settings.MEDIA_URL, 'review/audio/' + file_name)
    # with open(file_path, 'wb+') as destination:
    #     for chunk in file:
    #         destination.write(chunk)
    # return {'status': 'success', 'message': file_path}


def update_music_source(file, music_id, extension):
    file_name = str(music_id) + '.' + extension
    file_path = settings.MEDIA_URL
    if os.path.exists(file_path + 'review/audio/' + file_name):
        file_path += 'review/audio/' + file_name
    elif os.path.exists(file_path + 'common/audio/' + file_name):
        file_path += 'common/audio/' + file_name
    else:
        return {'status': 'fail', 'message': 'file does not exist'}
    os.remove(file_path)
    with open(file_path, 'wb+') as destination:
        for chunk in file:
            destination.write(chunk)
    return {'status': 'success', 'message': file_path}


# 方法已验证
def delete_music_source(music_id, extension):
    file_path = settings.MEDIA_URL
    file_name = str(music_id) + '.' + extension
    if os.path.exists(file_path + 'review/audio/' + file_name):
        file_path += 'review/audio/' + file_name
    elif os.path.exists(file_path + 'common/audio/' + file_name):
        file_path += 'common/audio/' + file_name
    else:
        return {'status': 'fail', 'message': 'file does not exists'}
    os.remove(file_path)
    return {'status': 'success', 'message': 'deleted file successfully'}


@csrf_exempt
# 接口已验证
def new_music_info(request):
    if not request.method == 'POST':
        return {'status': 'fail', 'message': 'Method not allowed'}
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User is not authenticated'})
    elif not request.FILES:
        return JsonResponse({'status': 'fail', 'message': 'No files uploaded'})

    # data = json.loads(request.body)
    data = request.POST.dict()

    if not set(data.keys()).issubset(authorization_items.music_info_to_update_by_user):
        return JsonResponse({'status': 'fail', 'message': 'Invalid items provided'})

    item_filter = dict(data)
    if None in item_filter.values() or None in item_filter.keys():
        return JsonResponse({'status': 'fail', 'message': 'Missing items provided'})

    file_list = {
        'audio': request.FILES['audio'],
        'lyric': request.FILES['lyric'],
        'cover': request.FILES['cover']
    }

    music_created = MusicInfo.objects.create(**item_filter)

    for file in file_list.values():
        music_response = new_file_source(file, music_created.music_id)
        if music_response['status'] != 'success':
            music_created.delete()
            return JsonResponse({'status': 'fail', 'message': music_response['message']})

        extension = file.name.split('.')[-1]
        if extension in authorization_items.allowed_upload_audio_type:
            music_created.source_extension = extension
        elif extension in authorization_items.allowed_upload_image_type:
            music_created.cover_extension = extension
        elif extension in authorization_items.allowed_upload_lyric_type:
            music_created.lyrics_extension = extension
    music_created.save()
    task_response = new_task(request, {
        'task_name': 'Music Info Review',
        'task_type': 'review.music',
        'task_priority': 0,
        'music_id': music_created.music_id
    })
    if task_response['status'] == 'fail':
        return JsonResponse({'status': 'fail', 'message': task_response['message']})
    else:
        return JsonResponse({'status': 'success', 'message': task_response['message']})


@csrf_exempt
# 接口已验证
def update_music_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'You are not authorized'})

    data = json.loads(request.body.decode('utf-8'))

    music_id = data.get('music_id', None)
    update_item = dict(data.get('update_item', None))

    now_user = CustomUser.objects.get(email=request.user.email)

    allowed_update_items = authorization_items.music_info_to_update_by_user

    if not MusicInfo.objects.filter(music_id=music_id).exists():
        return JsonResponse({'status': 'fail', 'message': 'Music does not exist'})
    elif not now_user.is_staff and not now_user.is_creator:
        return JsonResponse({'status': 'fail', 'message': 'You are not allowed to update this'})
    elif not now_user.is_active:
        return JsonResponse({'status': 'fail', 'message': 'You are not allowed to update this'})

    if now_user.is_staff:
        allowed_update_items = authorization_items.music_info_to_update_by_staff

    if not set(update_item.keys()).issubset(set(allowed_update_items)):
        return JsonResponse({'status': 'fail', 'message': 'Invalid update items'})
    elif None in update_item.keys() or None in update_item.values():
        return JsonResponse({'status': 'fail', 'message': 'Missing required parameters'})
    music_to_update = MusicInfo.objects.get(music_id=music_id)

    for key, value in update_item.items():
        setattr(music_to_update, key, value)
    music_to_update.save()
    return JsonResponse({'status': 'success', 'message': 'Music Info updated'})


@csrf_exempt
# 接口已验证
def delete_music_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User is not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'User is not staff'})

    data = json.loads(request.body.decode('utf-8'))
    music_id = data.get('music_id', None)

    if music_id is None:
        return JsonResponse({'status': 'fail', 'message': 'Missing required parameters'})
    elif not MusicInfo.objects.filter(music_id=music_id).exists():
        return JsonResponse({'status': 'fail', 'message': 'Music not found'})

    music_to_delete = MusicInfo.objects.get(music_id=music_id)
    response = delete_music_source(music_id, music_to_delete.extension)
    music_to_delete.delete()
    if response['status'] != 'success':
        return JsonResponse({'status': 'fail', 'message': response['message']})
    return JsonResponse({'status': 'success', 'message': 'Music Info'})


@csrf_exempt
# 接口已验证
def get_music_info(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User not authenticated'})

    select_item = request.GET.get('data', {})
    # 测试用，记得改回user可用的
    allowed_items = authorization_items.music_info_to_get_by_user
    if request.user.is_staff:
        allowed_items = authorization_items.music_info_to_get_by_staff

    if not set(select_item.keys()).issubset(set(allowed_items)):
        return JsonResponse({'status': 'fail', 'message': 'selected items not allowed'})
    elif None in select_item.values() or None in select_item.keys():
        return JsonResponse({'status': 'fail', 'message': 'Missing the required parameters'})

    if request.user.is_staff:
        response = list(MusicInfo.objects.filter(**select_item).values(*allowed_items))
    else:
        response = list(MusicInfo.objects.filter(**select_item, is_active=True, is_reviewed=True).values(*allowed_items))
    return JsonResponse({'status': 'success', 'message': response})


@csrf_exempt
def new_comment_info(request):
    pass
    # if not request.method == 'POST':
    #     return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    # elif not request.user.is_authenticated:
    #     return JsonResponse({'status': 'fail', 'message': 'User is not authenticated'})
    #
    # data = json.loads(request.body.decode('utf-8'))
    # content_id = data.get('content_id', None)
    # content_root_type = data.get('content_root_type', None)
    #
    # if content_id is None or content_root_type is None:
    #     return JsonResponse({'status': 'fail', 'message': 'Missing content_id or content_root_type'})
    #
    # if content_root_type == 'music':
    #     if not MusicInfo.objects.filter(music_id=content_id).exists():
    #         return JsonResponse({'status': 'fail', 'message': 'MusicInfo(root of comment) not found'})


@csrf_exempt
def delete_comment_info(request):
    pass


@csrf_exempt
def update_comment_info(request):
    pass


@csrf_exempt
def get_comment_info(request):
    pass


@csrf_exempt
# 接口已验证
def new_playlist_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method Not Allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User Not Authorized'})

    data = json.loads(request.body.decode('utf-8'))

    data = dict(data)

    if None in data.keys() or None in data.values():
        return JsonResponse({'status': 'fail', 'message': 'Missing data'})
    elif not set(data.keys()).issubset(set(authorization_items.music_list_item_to_update_by_user)):
        return JsonResponse({'status': 'fail', 'message': 'Invalid item'})

    music_list = []
    if 'music_list' in data.keys():
        music_list = data['music_list']
        data.pop('music_list')

    list_to_create = MusicPlayList.objects.create(**data, creator=CustomUser.objects.get(email=request.user.email))
    list_to_create.music_list.set(music_list)
    return JsonResponse({'status': 'success', 'message': 'Successfully created playlist'})


@csrf_exempt
# 接口已测试
def delete_playlist_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method Not Allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User Not Authorized'})

    data = json.loads(request.body.decode('utf-8'))
    list_id = data.get('list_id', None)

    if list_id is None:
        return JsonResponse({'status': 'error', 'message': 'Missing playlist_id'})
    elif not MusicPlayList.objects.filter(list_id=list_id).exists():
        return JsonResponse({'status': 'error', 'message': 'Playlist does not exist'})

    list_to_delete = MusicPlayList.objects.get(list_id=list_id)
    if CustomUser.objects.get(email=request.user.email) != list_to_delete.creator and not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'You do not have permission to delete this playlist'})
    list_to_delete.delete()
    return JsonResponse({'status': 'success', 'message': 'Deleted playlist successfully'})


@csrf_exempt
# 接口已测试
def update_playlist_info(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method Not Allowed'})
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User Not Authorized'})

    data = json.loads(request.body.decode('utf-8'))
    list_id = data.get('list_id', None)
    update_item = dict(data.get('update_item', None))

    if list_id is None:
        return JsonResponse({'status': 'fail', 'message': 'Missing playlist_id'})
    elif not MusicPlayList.objects.filter(list_id=list_id).exists():
        return JsonResponse({'error': 'fail', 'message': 'List does not exist'})

    allowed_item = authorization_items.music_list_item_to_update_by_user
    if request.user.is_staff:
        allowed_item = authorization_items.music_list_item_to_update_by_staff

    if not set(update_item.keys()).issubset(set(allowed_item)):
        return JsonResponse({'status': 'fail', 'message': 'Selected items not allowed to update'})
    elif None in update_item.values() or None in update_item.keys():
        return JsonResponse({'status': 'fail', 'message': 'Missing items selected'})

    playlist_to_update = MusicPlayList.objects.get(list_id=list_id)

    if playlist_to_update.creator != CustomUser.objects.get(email=request.user.email) and not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'You cannot edit this playlist'})

    if 'music_list' in update_item.keys():
        if type(update_item['music_list']) is not list:
            return JsonResponse({'status': 'fail', 'message': 'music_list must be a list'})
        music_list = update_item['music_list']
        for item in music_list:
            if not MusicInfo.objects.filter(music_id=item).exists():
                return JsonResponse({'status': 'fail', 'message': 'Invalid music in your music list'})
        for item in music_list:
            playlist_to_update.music_list.add(MusicInfo.objects.get(music_id=item))
        update_item.pop('music_list')

    for key, value in update_item.items():
        setattr(playlist_to_update, key, value)
    playlist_to_update.save()
    return JsonResponse({'status': 'success', 'message': 'Updated playlist successfully'})


@csrf_exempt
# 接口已测试
def get_playlist_info(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User is not authenticated'})

    selected_item = request.GET.get('selected_item', {})
    is_management = request.GET.get('is_management', None)

    user = CustomUser.objects.get(email=request.user.email)

    allowed_items = authorization_items.music_list_item_to_get_by_user
    if request.user.is_staff:
        allowed_items = authorization_items.music_list_item_to_get_by_staff

    if not set(selected_item.keys()).issubset(allowed_items):
        return JsonResponse({'status': 'fail', 'message': 'Selected item not allowed to filter by it'})
    elif None in selected_item.keys() or None in selected_item.values():
        return JsonResponse({'status': 'fail', 'message': 'Missing items selected'})

    if request.user.is_staff and is_management:
        playlist_to_select = list(MusicPlayList.objects.filter(**selected_item).values(*allowed_items))
    else:
        playlist_to_select = (
            list(MusicPlayList.objects.filter(**selected_item, is_public=True).exclude(creator=user).values(
                *allowed_items)))
        playlist_to_select += list(MusicPlayList.objects.filter(**selected_item, creator=user).values(*allowed_items))

    return JsonResponse({'status': 'success', 'message': playlist_to_select})


@csrf_exempt
def new_music_info_by_admin(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'status': 'fail', 'message': 'User is not staff'})

    uploaded_file = list(request.FILES.getlist('file'))

    if len(uploaded_file) == 0:
        return JsonResponse({'status': 'fail', 'message': 'You must upload an csv file'})

    uploaded_file = uploaded_file[0]

    if not uploaded_file.name.endswith('.csv'):
        return {'status': 'fail', 'message': 'File extension not allowed'}

    csv_data = uploaded_file.read().decode('gbk')
    csv_reader = csv.DictReader(csv_data.splitlines())

    for row in csv_reader:
        year = row['release_date']
        release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d").date()

        music_info = MusicInfo.objects.create(
            title=row.get('title'),
            album=row['album'],
            artist=row['artist'],
            release_date=release_date
        )
        music_info.save()

    return JsonResponse({'status': 'success', 'message': 'Music updated successfully'})
