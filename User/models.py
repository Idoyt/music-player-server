import uuid

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# 一些规则
# 1. 所有的id的长度均小于30
# 2. 所有的text的长度均小于300
# 3. 主键必须设置且unique且为Auto

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, primary_key=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, default='miku fans')
    avatar_url = models.URLField(default='', max_length=200, blank=True)

    follower_id_list = models.ManyToManyField(to='self', symmetrical=False, related_name='following')
    following_id_list = models.ManyToManyField(to='self', symmetrical=False, related_name='follower')
    dislikes_music = models.ManyToManyField('MusicInfo', related_name='disliked_by', blank=True)
    dislikes_list = models.ManyToManyField('MusicPlayList', related_name='disliked_by', blank=True)
    # 合法用户 (拥有听歌的权限，拥有创建歌单的权限，拥有收藏/点赞/评论/转发的权限)
    is_active = models.BooleanField(default=True)
    # 是管理员 (拥有封禁/解封管理员以外的用户的权限，拥有审查创作者上传的音乐的权限，拥有上传/修改音乐信息的权限)
    is_staff = models.BooleanField(default=False)
    # 是创作者 (拥有普通用户的所有权限以及上传音乐、歌词的权限)
    is_creator = models.BooleanField(default=False)

    to_be_deleted = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# 单个音频的所有信息
class MusicInfo(models.Model):
    music_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=30, default=None)
    artist = models.CharField(max_length=30, default=None)
    genre = models.CharField(max_length=30, default=None)
    album = models.CharField(max_length=30, default=None)
    extension = models.CharField(max_length=30, default=None)
    release_date = models.DateField(default=timezone.now)

    cover_url = models.URLField(max_length=200, default=None, null=True)
    source_url = models.URLField(max_length=200, default=None, null=True)
    lyrics_url = models.URLField(max_length=200, default=None, null=True)

    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    search_volume = models.IntegerField(default=0)
    # 评论数量可用MusicInfo.objects.get(music_id=music_id).comments.count()查询

    # 以下为仅 staff可获取字段
    is_active = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    # to_be_deleted = models.BooleanField(default=False)


class MusicPlayList(models.Model):
    list_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, primary_key=True)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    # type分为 none: 未设置, like: 我喜欢, created: 个人创建的, album: 专辑,
    list_type = models.CharField(max_length=30, default=None, null=True)

    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    # 评论数量可用 MusicPlayList.objects.get(music_id=music_id).comments.count()查询

    list_cover = models.URLField(max_length=200, default=None, null=True)
    list_name = models.CharField(max_length=30, default=None, null=True)
    create_date = models.DateField(auto_now_add=True)
    description = models.TextField(default=None, null=True)

    playback_volume = models.IntegerField(default=0)
    search_volume = models.IntegerField(default=0)
    music_list = models.ManyToManyField(to='MusicInfo', symmetrical=False, related_name='in_list', blank=True)
    is_reviewed = models.BooleanField(default=False)


class Comment(models.Model):
    comment_id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    father_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    father_comment_id_list \
        = models.ForeignKey('self', on_delete=models.CASCADE, related_name='son_comment_list', null=True)
    root_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='descendant_comments', null=True)
    root_is_music = models.BooleanField(default=False)
    playlist_root = models.ForeignKey(MusicPlayList, on_delete=models.CASCADE, related_name='comments', null=True)
    music_root = models.ForeignKey(MusicInfo, on_delete=models.CASCADE, related_name='comments', null=True)
    son_count = models.IntegerField(default=0)
    is_reviewed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    create_date = models.DateField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    user_like_this = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='liked_comment', null=True)
    content = models.TextField(default='none')


class Task(models.Model):
    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_name = models.CharField(max_length=30, default='Default Task')
    task_type = models.CharField(max_length=30)
    # task_priority的range为[0, 5]
    task_priority = models.IntegerField(default=0)
    task_tags = models.CharField(max_length=30, null=True)
    task_notes = models.TextField(null=True)

    task_creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tasks')
    create_date = models.DateField(auto_now_add=True)

    # 默认为 none , 未完成为 to be done, 完成为 completed, 失败为 failed
    task_state = models.CharField(max_length=30, default='to be done')
    task_completed_time = models.DateTimeField(default=timezone.now)
