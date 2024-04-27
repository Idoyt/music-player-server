import json
import os
import uuid
import User.authorization_items as authorization_items

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from Server import settings
from .models import CustomUser, MusicInfo, MusicPlayList, Comment, Task


# Create your views here.
@csrf_exempt
def login_view(request):
    if not request.method == 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Method Not Allowed'})
    elif request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User already logged in'})
    data = json.loads(request.body)
    email = data['email']
    password = data['password']
    user = authenticate(request, email=email, password=password)
    if user is None:
        return JsonResponse({'status': 'fail', 'message': 'User does not exist'})
    login(request, user)
    return JsonResponse({'status': 'success', 'message': 'Login'})


@csrf_exempt
def logout_view(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    logout(request)
    return JsonResponse({'status': 'success', 'message': 'logged out'})


@csrf_exempt
def check_email_view(request):
    if request.method == 'POST':
        print(request.POST)
        data = json.loads(request.body)
        email = data['email']
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'success', 'message': 'email check successful'})
        else:
            return JsonResponse({'status': 'fail', 'message': 'user does not exist'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'method not allowed'})


# 查找是否与已有音频重复
def has_duplicate_music(data):
    return \
        MusicInfo.objects.filter(title=data['title'], artist=data['artist'], album=data['album']).exists()


# 以下为各种增删改查函数

# 任务的增删改查
def new_task(request, data):
    if not request.method == 'POST':
        return {'status': 'fail', 'message': 'Method not allowed'}
    elif not request.user.is_authenticated:
        return {'status': 'fail', 'message': 'User is not authenticated'}
    elif not request.user.is_staff:
        return {'status': 'fail', 'message': 'Only staff users can create tasks'}
    elif data['type'] not in authorization_items.task_type:
        return {'status': 'fail', 'message': 'Task type not allowed'}

    task_name = data['task_name']
    task_type = data['type']
    task_priority = data['priority']
    task_tags = data['task_tags']

    task_creator = CustomUser.objects.get(email=request.user.email).uuid
    task_notes = data['task_notes']
    task_status = 'to be done'

    new_tasks = Task.objects.create(
        task_name=task_name,
        task_type=task_type,
        task_priority=task_priority,
        task_tags=task_tags,
        task_creator=task_creator,
        task_notes=task_notes,
        task_status=task_status
    )
    new_tasks.save()
    return {'status': 'success', 'message': 'Task created successfully'}


def update_task(data):
    task_id = data['task_id']
    # example: {'task_name': 'task name example', .....}
    update_item = dict(data['update_item'])
    if not Task.objects.filter(task_id=task_id).exists():
        return {'status': 'fail', 'message': 'task not found'}
    elif update_item.keys() != authorization_items.task_update_item:
        return {'status': 'fail', 'message': 'Item not allowed to change'}
    task_to_update = Task.objects.get(task_id=task_id)
    for key, value in update_item.items():
        setattr(task_to_update, key, value)
    return {'status': 'success', 'message': 'Task updated successfully'}


@csrf_exempt
def delete_task(request):
    data = json.loads(request.body)
    task_id_list = data['task_id_list']
    if not request.method == 'POST':
        return {'status': 'fail', 'message': 'Method not allowed'}
    elif not request.user.is_authenticated:
        return {'status': 'fail', 'message': 'User is not authenticated'}
    elif not request.user.is_staff:
        return {'status': 'fail', 'message': 'User is not staff users can delete'}
    elif len(task_id_list) == 0:
        return {'status': 'fail', 'message': 'Task list empty'}
    elif len(task_id_list) > 100:
        return {'status': 'fail', 'message': 'Task list to delete too long'}
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
        task.delete()
    message = 'Task'
    if length > 1:
        message = 'Tasks'
    return {'status': 'success', 'message': message + ' deleted successfully'}


@csrf_exempt
def get_tasks(request):
    if not request.method == 'GET':
        return {'status': 'fail', 'message': 'Method not allowed'}
    elif request.user.is_authenticated:
        return {'status': 'fail', 'message': 'User is authenticated'}
    elif request.user.is_staff:
        return {'status': 'fail', 'message': 'You are not authorized to get tasks list'}

    data = json.loads(request.body.decode('utf-8'))
    task_id = data['task_id']
    # 写到这里了
    type = data['task_type']



# 用户信息的增删改查
@csrf_exempt
def new_user_info(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data['email']
        password = data['password']
        username = data['username']
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'fail', 'message': 'email has been taken'})
        else:
            CustomUser.objects.create_user(email=email, password=password, username=username)
            return JsonResponse({'status': 'success', 'message': 'user registered successfully'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'method is not allowed'})


@csrf_exempt
def update_user_info(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        update_item = data['update_item']
        update_value = data['update_value']

        now_user = CustomUser.objects.get(email=request.user.email)

        # 可修改项目，需要和 models 里统一起来
        allowed_update_items = authorization_items.user_info_user

        if not request.user.is_authenticated:
            return JsonResponse({'status': 'fail', 'message': 'user not authenticated'})
        elif not now_user.exists:
            return JsonResponse({'status': 'fail', 'message': 'user does not exist'})
        if request.user.is_staff:
            allowed_update_items = authorization_items.user_info_staff

        if now_user.is_staff:
            return JsonResponse({'status': 'fail', 'message': 'staff info not allowed to be updated'})
        else:
            if update_item not in allowed_update_items:
                return JsonResponse({'status': 'fail', 'message': 'update item not allowed'})
            else:
                setattr(now_user, update_item, update_value)
                now_user.save()
                return JsonResponse({'status': 'success', 'message': 'update item successfully'})

    else:
        return JsonResponse({'status': 'fail', 'message': 'method not allowed'})


@csrf_exempt
def delete_user_info(request):
    if not request.method == 'GET':
        return JsonResponse({'status': 'fail', 'message': 'Method not allowed'})
    elif not request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'message': 'User not authenticated'})

    data = json.loads(request.body.decode('utf-8'))
    email = data['email']
    if request.user.is_staff:
        user_to_delete = CustomUser.objects.get(email=email)
        if user_to_delete.is_staff:
            return JsonResponse({'status': 'fail', 'message': 'You are not allowed to delete staff info'})
        elif not user_to_delete.exists:
            return JsonResponse({'status': 'fail', 'message': 'User to delete does not exist'})
        user_to_delete.delete()
        return JsonResponse({'status': 'success', 'message': 'User successfully deleted'})
    else:
        email = request.user.email
        user_to_delete = CustomUser.objects.get(email=email)
        user_to_delete['to_be_deleted'] = True
        user_to_delete.save()
        return JsonResponse({'status': 'success', 'message': 'delete request has been submitted'})


@csrf_exempt
def get_user_info(request):
    if request.method == 'GET':
        data = json.loads(request.body)
        email = data['email']
        if CustomUser.objects.filter(email=email).exists and request.user.is_authenticated and request.user.is_active:
            user = CustomUser.objects.get(email=email)
            response = {
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


# 增删改音频源文件
def music_source(file, music_id, option):
    file_name = music_id
    if not file.endwith(authorization_items.music_source_type):
        return {'status': 'fail', 'message': 'file extension not allowed'}

    if option == 'new':
        file_path = os.path.join(settings.MEDIA_URL, 'review/' + file_name)
        with open(file_path + 'review/' + file_name, 'w+') as destination:
            for chunk in file:
                destination.write(chunk)
        return {'status': 'success', 'message': file_path + file_name}
    # 只有审核通过的音源才可以被更新，并重新放到待审核区；未经审核的也会在更新音源后放到待审核区
    elif option == 'update':
        file_path = settings.MEDIA_URL
        if os.path.exists(file_path + 'review/' + file_name):
            file_path += 'review/' + file_name
        elif os.path.exists(file_path + 'common/' + file_name):
            file_path += 'common/' + file_name
        else:
            return {'status': 'fail', 'message': 'file does not exist'}
        os.remove(file_path)
        with open(file_path, 'w+') as destination:
            for chunk in file:
                destination.write(chunk)
        return {'status': 'success', 'message': file_path}

    elif option == 'delete':
        file_path = settings.MEDIA_URL
        if os.path.exists(file_path + 'review/' + file_name):
            file_path += 'review/' + file_name
        elif os.path.exists(file_path + 'common/' + file_name):
            file_path += 'common/' + file_name
        else:
            return {'status': 'fail', 'message': 'file does not exists'}
        os.remove(file_path)
        return {'status': 'success', 'message': 'deleted file successfully'}
    else:
        return {'status': 'fail', 'message': 'Option not found'}


@csrf_exempt
def new_music_info(request):
    # 传来的参数没有加校验功能，以后再说
    if request.method == 'POST':
        data = json.loads(request.body)
        music_id = uuid.uuid4()
        title = data['title']
        artist = data['artist']
        album = data['album']
        genre = data['genre']
        release_data = data['release_data']

        if not request.user.is_authenticated:
            return JsonResponse({'status': 'fail', 'message': 'User is not authenticated'})
        elif None in [title, artist, album, release_data, genre]:
            return JsonResponse({
                'status': 'fail',
                'message': 'Please provide all required fields(title, artist, album, release, genre)'
            })
        elif has_duplicate_music(data):
            return JsonResponse({'status': 'fail', 'message': 'Music already uploaded'})

        file = request.FILES['file']
        music_url = music_source(file, music_id, 'new')
        MusicInfo.objects.create(
            music_id=music_id,
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            release_data=release_data,
            source_url=music_url,
        )


@csrf_exempt
def update_music_info(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        music_id = data['music_id']
        update_item = data['update_item']
        update_value = data['update_value']
        now_user = CustomUser.objects.get(email=request.user.email)

        allowed_update_items = authorization_items.music_info_user

        if not request.user.is_authenticated:
            return JsonResponse({'status': 'fail', 'message': 'You are not authorized'})
        elif not MusicInfo.objects.filter(music_id=music_id).exists():
            return JsonResponse({'status': 'fail', 'message': 'Music does not exist'})
        elif not now_user.is_staff or not now_user.is_creator:
            return JsonResponse({'status': 'fail', 'message': 'You are not allowed to update this'})
        elif not now_user.is_active and now_user.is_creator:
            return JsonResponse({'status': 'fail', 'message': 'You are not allowed to update this'})

        if request.user.is_staff:
            allowed_update_items = authorization_items.music_info_staff

        if update_item not in allowed_update_items:
            return JsonResponse({'error': 'Only staff or creator can update music information'})
        else:
            music_to_update = MusicInfo.objects.get(music_id=music_id)
            setattr(music_to_update, update_item, update_value)
            music_to_update.save()
            return JsonResponse({'status': 'success', 'message': 'Music Info updated'})
    else:
        return JsonResponse({'error': 'Method not allowed'})


@csrf_exempt
def update_comment_info(request):
    pass


@csrf_exempt
def update_playlist_info(request):
    pass
