import json
import os
from django.contrib.auth.hashers import check_password
import User.authorization_items as authorization_items
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Server import settings
from .models import CustomUser, MusicInfo, MusicPlayList, Comment, Task


# 2024.4.28 记， 1. 记得将所有的delete、review操作添加 new task操作 2. 继续测试update_user_info接口
# 2024.4.29 记， 1. 在delete_task视图中添加删除task后的回滚操作

@csrf_exempt
# 接口已验证
def login_view(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'Method Not Allowed'})

    data = json.loads(request.body)
    email = data.get('email', None)
    password = data.get('password', None)
    user = authenticate(request, email=email, password=password)
    if email is None or password is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing credentials'})
    elif request.user.is_authenticated and email == request.user.email:
        return JsonResponse({'state': 'fail', 'message': 'User already logged in'})
    elif user is None:
        return JsonResponse({'state': 'fail', 'message': 'Email or Password is incorrect'})

    login(request, user)
    return JsonResponse({'state': 'success', 'message': 'Login'})


@csrf_exempt
# 接口已验证
def logout_view(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User does not login'})
    logout(request)
    return JsonResponse({'state': 'success', 'message': 'logged out'})


@csrf_exempt
def check_login(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})

    data = json.loads(request.body.decode('utf-8'))
    email = data.get('email', None)
    if email is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing parameters'})

    user = CustomUser.objects.get(email=email)
    if user.is_authenticated:
        return JsonResponse({'state': 'success', 'message': 'User logged in successfully'})
    else:
        return JsonResponse({'state': 'fail', 'message': 'User does not exist or is not authenticated'})

@csrf_exempt
# 接口已验证
def check_email_view(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'method not allowed'})

    data = json.loads(request.body)
    email = data.get('email', None)
    if email is None:
        return JsonResponse({'state': 'fail', 'message': 'Email is required'})
    elif not CustomUser.objects.filter(email=email).exists():
        return JsonResponse({'state': 'fail', 'message': 'Email is not registered'})

    return JsonResponse({'state': 'success', 'message': 'email check successful'})


# 以下为各种增删改查函数

# 任务的增删改查
# data 所需格式为
# {'task_name': value, 'task_type': value, 'task_priority': value, 'task_tags': value, 'task_notes': value}
# 此方法已验证
def new_task(request, data):
    if not request.user.is_authenticated:
        return {'state': 'fail', 'message': 'User is not authenticated'}
    elif not data.get('task_type') in authorization_items.task_type:
        return {'state': 'fail', 'message': 'Task type not allowed'}

    task_name = data.get('task_name', 'Default Task')
    task_type = data.get('task_type')
    task_priority = data.get('task_priority', 0)
    task_tags = data.get('task_tags', None)

    task_creator = CustomUser.objects.get(email=request.user.email)
    task_notes = data.get('task_notes', None)
    task_state = 'to be done'

    new_tasks = Task.objects.create(
        task_name=task_name,
        task_type=task_type,
        task_priority=task_priority,
        task_tags=task_tags,
        task_creator=task_creator,
        task_notes=task_notes,
        task_state=task_state
    )
    new_tasks.save()
    return {'state': 'success', 'message': 'Task created successfully'}


@csrf_exempt
# 此接口已验证
def update_task(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User is not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'state': 'fail', 'message': 'Only staff can update task'})

    data = json.loads(request.body.decode('utf-8'))
    task_id = data.get('task_id', None)
    # example: {'task_name': 'task name example', .....}
    update_item = dict(data.get('update_item', None))

    if task_id is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing task_id'})
    elif update_item is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing update_item'})
    elif not Task.objects.filter(task_id=task_id).exists():
        return JsonResponse({'state': 'fail', 'message': 'task not found'})
    elif not set(update_item.keys()).issubset(authorization_items.task_update_item):
        return JsonResponse({'state': 'fail', 'message': 'Item not allowed to change'})

    task_to_update = Task.objects.get(task_id=task_id)
    repeat = {}
    for key, value in update_item.items():
        if getattr(task_to_update, key) == value:
            repeat[key] = value
            continue
        setattr(task_to_update, key, value)
    task_to_update.save()

    if len(repeat) == len(update_item.keys()):
        return JsonResponse({'state': 'fail', 'message': 'All value to update repeat'})
    elif len(repeat) < len(update_item.keys()):
        return JsonResponse({
            'state': 'success',
            'message': {'description': 'Update success, but some values repeat as followed: ', 'value': repeat}
        })
    return JsonResponse({'state': 'success', 'message': 'Task updated successfully'})


@csrf_exempt
def delete_task(request):
    data = json.loads(request.body.decode('utf-8'))
    task_id_list = data.get('task_id_list', None)

    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User is not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'state': 'fail', 'message': 'User is not staff users can delete'})
    elif len(task_id_list) == 0:
        return JsonResponse({'state': 'fail', 'message': 'Task list empty'})
    elif len(task_id_list) > 100:
        return JsonResponse({'state': 'fail', 'message': 'Task list to delete too long'})
    length = len(task_id_list)

    for task_id in task_id_list:
        task = Task.objects.get(id=task_id)
        if task is None:
            return {
                'state': 'fail',
                'message': 'task not found in index:' + task_id_list.index(task_id) + 'in task list'
            }
    for task_id in task_id_list:
        task = Task.objects.get(id=task_id)
        # 在这里添加rollback相关代码
        task.delete()
    message = 'Task'
    if length > 1:
        message = 'Tasks'
    return JsonResponse({'state': 'success', 'message': message + ' deleted successfully'})


@csrf_exempt
# 此接口已验证
def get_task(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User is authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'state': 'fail', 'message': 'You are not authorized to get tasks list'})

    data = json.loads(request.body.decode('utf-8'))

    data = dict(data)

    select_item = list(data.keys())
    if not set(select_item).issubset(authorization_items.task_item_to_get):
        return JsonResponse({'state': 'fail', 'message': 'Invalid item for selecting tasks'})

    inquiry_filter = {}
    for key, value in data.items():
        if data[key] is None:
            continue
        inquiry_filter[key] = value
    print(inquiry_filter)
    response = Task.objects.filter(**inquiry_filter).values()
    return JsonResponse({'state': 'success', 'message': list(response)})


# 用户信息的增删改查
@csrf_exempt
# 接口已验证
def new_user_info(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'method is not allowed'})
    data = json.loads(request.body)
    email = data.get('email', None)
    password = data.get('password', None)
    username = data.get('username', None)
    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse({'state': 'fail', 'message': 'email has been taken'})
    else:
        CustomUser.objects.create_user(email=email, password=password, username=username)
        return JsonResponse({'state': 'success', 'message': 'user registered successfully'})


@csrf_exempt
# 接口已验证
def update_user_info(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User not authenticated'})

    data = json.loads(request.body.decode('utf-8'))
    update_item = data.get('update_item', None)
    update_value = data.get('update_value', None)

    user_to_update = CustomUser.objects.get(email=request.user.email)
    allowed_update_items = authorization_items.user_info_user

    if not CustomUser.objects.filter(email=request.user.email).exists():
        return JsonResponse({'state': 'fail', 'message': 'User does not exist'})
    elif user_to_update.is_staff:
        return JsonResponse({'state': 'fail', 'message': 'staff info not allowed to be updated'})
    elif request.user.is_staff:
        allowed_update_items = authorization_items.user_info_staff
    if update_item not in allowed_update_items:
        return JsonResponse({'state': 'fail', 'message': 'update item not allowed'})
    elif update_value is None or update_item is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing parameter'})
    elif getattr(user_to_update, update_item) == update_value and update_item != 'password':
        return JsonResponse({'state': 'fail', 'message': 'Repeated update'})

    if update_item == 'password':
        if check_password(update_value, request.user.password):
            return JsonResponse({'state': 'fail', 'message': 'Repeated update'})
        user_to_update.set_password(update_value)
    else:
        setattr(user_to_update, update_item, update_value)
    user_to_update.save()
    return JsonResponse({'state': 'success', 'message': 'update item successfully'})


# 策略： 普通用户可以提交删除本人账户的task，staff用户可以直接删除除了自己以外的所有用户
@csrf_exempt
# 接口已验证
def delete_user_info(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User not authenticated'})

    data = json.loads(request.body.decode('utf-8'))
    email = data.get('email', None)
    if request.user.is_staff:
        if email is None:
            return JsonResponse({'state': 'fail', 'message': 'Missing email'})
        elif not CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'state': 'fail', 'message': 'User to delete does not exist'})

        user_to_delete = CustomUser.objects.get(email=email)

        if user_to_delete.email == request.user.email:
            return JsonResponse({'state': 'fail', 'message': 'You can not delete yourself'})

        user_to_delete.delete()
        return JsonResponse({'state': 'success', 'message': 'User successfully deleted'})
    else:
        email = request.user.email
        user_to_delete = CustomUser.objects.get(email=email)
        if user_to_delete.to_be_deleted:
            return JsonResponse({'state': 'fail', 'message': 'You have already submitted your delete task'})

        user_to_delete.to_be_deleted = True
        user_to_delete.save()

        task_response = new_task(request, {'task_name': '测试用task', 'task_type': 'delete', 'task_priority': 1})
        if task_response['state'] == 'fail':
            return JsonResponse({'state': 'fail', 'message': task_response['message']})
        else:
            return JsonResponse({'state': 'success', 'message': 'delete request has been submitted'})


@csrf_exempt
# 接口已验证
def get_user_info(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'You are logged in'})

    if request.user.is_staff:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', None)
        if email is None:
            email = request.user.email

        if not CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'state': 'fail', 'message': 'Email not found'})

        user = CustomUser.objects.get(email=email)
        response = {
            'email': user.email,
            'username': user.username,
            'avatar_url': user.avatar_url,
            'is_creator': user.is_creator,
            'follower_id_list': list(user.follower_id_list.values()),
            'following_id_list': list(user.following_id_list.values()),
            'dislikes_music': list(user.dislikes_music.values()),
            'dislikes_list': list(user.dislikes_list.values()),

            'uuid': user.uuid,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'to_be_deleted': user.to_be_deleted
        }
        return JsonResponse({'state': 'success', 'message': response})

    else:
        user = CustomUser.objects.get(email=request.user.email)
        if not user.is_active:
            return JsonResponse({'state': 'fail', 'message': 'You have been banned'})

        response = {
            'email': user.email,
            'username': user.username,
            'avatar_url': user.avatar_url,
            'is_creator': user.is_creator,
            'follower_id_list': list(user.follower_id_list.values()),
            'following_id_list': list(user.following_id_list.values()),
            'dislikes_music': list(user.dislikes_music.values()),
            'dislikes_list': list(user.dislikes_list.values()),
        }
        return JsonResponse({'state': 'success', 'message': response})


# 增删改音频源文件
# 方法已验证
def new_music_source(file, music_id, extension):
    file_name = str(music_id) + '.' + extension
    if extension not in authorization_items.music_source_type:
        return {'state': 'fail', 'message': 'file extension not allowed'}

    file_path = os.path.join(settings.MEDIA_URL, 'review/audio/' + file_name)
    with open(file_path, 'wb+') as destination:
        for chunk in file:
            destination.write(chunk)
    return {'state': 'success', 'message': file_path}


def update_music_source(file, music_id, extension):
    file_name = str(music_id) + '.' + extension
    file_path = settings.MEDIA_URL
    if os.path.exists(file_path + 'review/audio/' + file_name):
        file_path += 'review/audio/' + file_name
    elif os.path.exists(file_path + 'common/audio/' + file_name):
        file_path += 'common/audio/' + file_name
    else:
        return {'state': 'fail', 'message': 'file does not exist'}
    os.remove(file_path)
    with open(file_path, 'wb+') as destination:
        for chunk in file:
            destination.write(chunk)
    return {'state': 'success', 'message': file_path}


# 方法已验证
def delete_music_source(music_id, extension):
    file_path = settings.MEDIA_URL
    file_name = str(music_id) + '.' + extension
    if os.path.exists(file_path + 'review/audio/' + file_name):
        file_path += 'review/audio/' + file_name
    elif os.path.exists(file_path + 'common/audio/' + file_name):
        file_path += 'common/audio/' + file_name
    else:
        return {'state': 'fail', 'message': 'file does not exists'}
    os.remove(file_path)
    return {'state': 'success', 'message': 'deleted file successfully'}


@csrf_exempt
# 接口已验证
def new_music_info(request):
    # 传来的参数没有加校验功能，以后再说
    if not request.method == 'POST':
        return {'state': 'fail', 'message': 'Method not allowed'}
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User is not authenticated'})
    elif not request.FILES:
        return JsonResponse({'state': 'fail', 'message': 'No files uploaded'})

    # data = json.loads(request.body)
    data = request.POST.dict()

    if not set(data.keys()).issubset(authorization_items.music_info_to_update_by_user):
        return JsonResponse({'state': 'fail', 'message': 'Invalid items provided'})

    item_filter = {}
    for key, value in data.items():
        if key is None or value is None:
            return JsonResponse({'state': 'fail', 'message': 'Missing items provided'})
        item_filter[key] = value

    file = next(iter(request.FILES.values()))
    item_filter['extension'] = file.name.split('.')[-1].lower()
    music_created = MusicInfo.objects.create(**item_filter)

    response = new_music_source(file, music_created.music_id, music_created.extension)
    if response['state'] != 'success':
        music_created.delete()
        return JsonResponse({'state': 'fail', 'message': response['message']})

    music_created.source_url = response['message']
    music_created.save()
    return JsonResponse({'state': 'success', 'message': 'Create music info and submit it to review successfully'})


@csrf_exempt
# 接口已验证
def update_music_info(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'You are not authorized'})

    data = json.loads(request.body.decode('utf-8'))

    music_id = data.get('music_id', None)
    update_item = dict(data.get('update_item', None))

    now_user = CustomUser.objects.get(email=request.user.email)

    allowed_update_items = authorization_items.music_info_to_update_by_user

    if not MusicInfo.objects.filter(music_id=music_id).exists():
        return JsonResponse({'state': 'fail', 'message': 'Music does not exist'})
    elif not now_user.is_staff and not now_user.is_creator:
        return JsonResponse({'state': 'fail', 'message': 'You are not allowed to update this'})
    elif not now_user.is_active:
        return JsonResponse({'state': 'fail', 'message': 'You are not allowed to update this'})

    if now_user.is_staff:
        allowed_update_items = authorization_items.music_info_to_update_by_staff

    if not set(update_item.keys()).issubset(set(allowed_update_items)):
        return JsonResponse({'state': 'fail', 'message': 'Invalid update items'})
    elif None in update_item.keys() or None in update_item.values():
        return JsonResponse({'state': 'fail', 'message': 'Missing required parameters'})
    music_to_update = MusicInfo.objects.get(music_id=music_id)

    for key, value in update_item.items():
        setattr(music_to_update, key, value)
    music_to_update.save()
    return JsonResponse({'state': 'success', 'message': 'Music Info updated'})


@csrf_exempt
# 接口已验证
def delete_music_info(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User is not authenticated'})
    elif not request.user.is_staff:
        return JsonResponse({'state': 'fail', 'message': 'User is not staff'})

    data = json.loads(request.body.decode('utf-8'))
    music_id = data.get('music_id', None)

    if music_id is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing required parameters'})
    elif not MusicInfo.objects.filter(music_id=music_id).exists():
        return JsonResponse({'state': 'fail', 'message': 'Music not found'})

    music_to_delete = MusicInfo.objects.get(music_id=music_id)
    response = delete_music_source(music_id, music_to_delete.extension)
    music_to_delete.delete()
    if response['state'] != 'success':
        return JsonResponse({'state': 'fail', 'message': response['message']})
    return JsonResponse({'state': 'success', 'message': 'Music Info'})


@csrf_exempt
# 接口已验证
def get_music_info(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'fail', 'message': 'User not authenticated'})

    data = json.loads(request.body.decode('utf-8'))
    select_item = dict(data)

    allowed_items = authorization_items.music_info_to_update_by_user
    if request.user.is_staff:
        allowed_items = authorization_items.music_info_to_update_by_staff

    if not set(select_item.keys()).issubset(set(allowed_items)):
        return JsonResponse({'state': 'fail', 'message': 'selected items not allowed'})
    elif None in select_item.values() or None in select_item.keys():
        return JsonResponse({'state': 'fail', 'message': 'Missing the required parameters'})

    response = []
    if request.user.is_staff:
        music_to_select = MusicInfo.objects.filter(**select_item)
    else:
        music_to_select = MusicInfo.objects.filter(**select_item, is_active=True, is_reviewed=True)

    for audio in list(music_to_select.values()):
        result = {key: value for key, value in audio.items() if key in authorization_items.music_info_to_get_by_user}
        response.append(result)
    return JsonResponse({'state': 'success', 'message': response})


@csrf_exempt
def new_comment_info(request):
    pass
    # if not request.method == 'POST':
    #     return JsonResponse({'state': 'fail', 'message': 'Method not allowed'})
    # elif not request.user.is_authenticated:
    #     return JsonResponse({'state': 'fail', 'message': 'User is not authenticated'})
    #
    # data = json.loads(request.body.decode('utf-8'))
    # content_id = data.get('content_id', None)
    # content_root_type = data.get('content_root_type', None)
    #
    # if content_id is None or content_root_type is None:
    #     return JsonResponse({'state': 'fail', 'message': 'Missing content_id or content_root_type'})
    #
    # if content_root_type == 'music':
    #     if not MusicInfo.objects.filter(music_id=content_id).exists():
    #         return JsonResponse({'state': 'fail', 'message': 'MusicInfo(root of comment) not found'})


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
        return JsonResponse({'state': 'error', 'message': 'Method Not Allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'error', 'message': 'User Not Authorized'})

    data = json.loads(request.body.decode('utf-8'))
    data = dict(data)

    if None in data.keys() or None in data.values():
        return JsonResponse({'state': 'error', 'message': 'Missing data'})
    elif not set(data.keys()).issubset(set(authorization_items.music_list_item_to_update_by_user)):
        return JsonResponse({'state': 'error', 'message': 'Invalid item'})

    MusicPlayList.objects.create(**data, creator=CustomUser.objects.get(email=request.user.email))
    return JsonResponse({'state': 'success', 'message': 'Successfully created playlist'})


@csrf_exempt
# 接口已测试
def delete_playlist_info(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'error', 'message': 'Method Not Allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'error', 'message': 'User Not Authorized'})

    data = json.loads(request.body.decode('utf-8'))
    list_id = data.get('list_id', None)

    if list_id is None:
        return JsonResponse({'state': 'error', 'message': 'Missing playlist_id'})
    elif not MusicPlayList.objects.filter(list_id=list_id).exists():
        return JsonResponse({'state': 'error', 'message': 'Playlist does not exist'})

    list_to_delete = MusicPlayList.objects.get(list_id=list_id)
    if CustomUser.objects.get(email=request.user.email) != list_to_delete.creator and not request.user.is_staff:
        return JsonResponse({'state': 'error', 'message': 'You do not have permission to delete this playlist'})
    list_to_delete.delete()
    return JsonResponse({'state': 'success', 'message': 'Deleted playlist successfully'})


@csrf_exempt
# 接口已测试
def update_playlist_info(request):
    if not request.method == 'POST':
        return JsonResponse({'state': 'error', 'message': 'Method Not Allowed'})
    if not request.user.is_authenticated:
        return JsonResponse({'state': 'error', 'message': 'User Not Authorized'})

    data = json.loads(request.body.decode('utf-8'))
    list_id = data.get('list_id', None)
    update_item = dict(data.get('update_item', None))

    if list_id is None:
        return JsonResponse({'state': 'fail', 'message': 'Missing playlist_id'})
    elif not MusicPlayList.objects.filter(list_id=list_id).exists():
        return JsonResponse({'error': 'fail', 'message': 'List does not exist'})

    allowed_item = authorization_items.music_list_item_to_update_by_user
    if request.user.is_staff:
        allowed_item = authorization_items.music_list_item_to_update_by_staff

    if not set(update_item.keys()).issubset(set(allowed_item)):
        return JsonResponse({'state': 'fail', 'message': 'Selected items not allowed to update'})
    elif None in update_item.values() or None in update_item.keys():
        return JsonResponse({'state': 'fail', 'message': 'Missing items selected'})

    playlist_to_update = MusicPlayList.objects.get(list_id=list_id)

    if playlist_to_update.creator != CustomUser.objects.get(email=request.user.email) and not request.user.is_staff:
        return JsonResponse({'state': 'fail', 'message': 'You cannot edit this playlist'})

    if 'music_list' in update_item.keys():
        if type(update_item['music_list']) is not list:
            return JsonResponse({'state': 'fail', 'message': 'music_list must be a list'})
        music_list = update_item['music_list']
        for item in music_list:
            if not MusicInfo.objects.filter(music_id=item).exists():
                return JsonResponse({'state': 'fail', 'message': 'Invalid music in your music list'})
        for item in music_list:
            playlist_to_update.music_list.add(MusicInfo.objects.get(music_id=item))
        update_item.pop('music_list')

    for key,value in update_item.items():
        setattr(playlist_to_update, key, value)
    playlist_to_update.save()
    return JsonResponse({'state': 'success', 'message': 'Updated playlist successfully'})


@csrf_exempt
# 接口已测试
def get_playlist_info(request):
    if not request.method == 'GET':
        return JsonResponse({'state': 'error', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'state': 'error', 'message': 'User is not authenticated'})

    data = json.loads(request.body.decode('utf-8'))
    data = dict(data)
    user = CustomUser.objects.get(email=request.user.email)

    allowed_items = authorization_items.music_list_item_to_get_by_user
    if request.user.is_staff:
        allowed_items = authorization_items.music_list_item_to_get_by_staff

    if not set(data.keys()).issubset(allowed_items):
        return JsonResponse({'state': 'fail', 'message': 'Selected item not allowed to filter by it'})
    elif None in data.keys() or None in data.values():
        return JsonResponse({'state': 'fail', 'message': 'Missing items selected'})

    response = []
    if request.user.is_staff:
        response = list(MusicPlayList.objects.filter(**data).values())
    else:
        playlist_to_select = list(MusicPlayList.objects.filter(**data, is_public=True).exclude(creator=user).values())
        playlist_to_select += list(MusicPlayList.objects.filter(**data, creator=user).values())

        for playlist in playlist_to_select:
            result = {}
            for key, value in playlist.items():
                result = {key: value for key, value in playlist.items() if
                          key in authorization_items.music_list_item_to_get_by_user}
            response.append(result)

    return JsonResponse({'state': 'success', 'message': response})


@csrf_exempt
def new_avatar_url(request):
    pass


@csrf_exempt
def delete_avatar_url(request):
    pass


@csrf_exempt
def update_avatar_url(request):
    pass
