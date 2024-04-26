import uuid
from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# 一些规则
# 1. 所有的id的长度均小于30
# 2. 所有的text的长度均小于300
# 3. 主键必须设置且unique且为Auto

# 2024.4.25 21:11记 把Arrary相关的词条全换了，MySql不支持这个！！！！！
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

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, default='miku fans')
    avatar = models.URLField(default='', max_length=200, blank=True)

    fans_id_list = models.ManyToManyField(to='self', symmetrical=False, related_name='following')
    following_id_list = models.ManyToManyField(to='self', symmetrical=False, related_name='follower')

    # 合法用户 (拥有听歌的权限，拥有创建歌单的权限，拥有收藏/点赞/评论/转发的权限)
    is_active = models.BooleanField(default=True)
    # 是管理员 (拥有封禁/解封管理员以外的用户的权限，拥有审查创作者上传的音乐的权限，拥有上传/修改音乐信息的权限)
    is_staff = models.BooleanField(default=False)
    # 是创作者 (拥有普通用户的所有权限以及上传音乐、歌词的权限)
    is_creator = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# 单个音频的所有信息
class MusicInfo(models.Model):
    music_id = models.AutoField(primary_key=True, unique=True)
    title = models.CharField(max_length=30, default='none')
    artist = models.CharField(max_length=30, default='none')
    genre = models.CharField(max_length=30, default='none')
    album = models.CharField(max_length=30, default='none')

    cover = models.URLField(max_length=200, default='none')
    source_url = models.URLField(max_length=200, default='none')
    lyrics_url = models.URLField(max_length=200, default='none')

    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)

    # releaseDate = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


# 新增评论时记得携带list/music的id
class MusicPlayList(models.Model):
    list_id = models.AutoField(primary_key=True, unique=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    # type分为 none: 未设置, like: 我喜欢, created: 个人创建的, album: 专辑,
    list_type = models.CharField(max_length=30, default='none')

    list_cover = models.URLField(max_length=200, default='none')
    list_name = models.CharField(max_length=30, default='none')
    create_date = models.DateField(auto_now_add=True)
    description = models.TextField(default='none')

    playback_volume = models.IntegerField(default=0)


class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True, unique=True)
    father_comment = models.CharField(max_length=30, default='none')
    father_comment_id_list = models.ForeignKey('self', on_delete=models.CASCADE, related_name='son_comments', null=True)
    root_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='descendant_comments', null=True)
    root_is_music = models.BooleanField(default=False)
    playlist_root = models.ForeignKey(MusicPlayList, on_delete=models.CASCADE, related_name='comments', null=True)
    music_root = models.ForeignKey(MusicInfo, on_delete=models.CASCADE, related_name='comments', null=True)

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    create_date = models.DateField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    son_count = models.IntegerField(default=0)
    content = models.TextField(default='none')

class UserFavorite(models.Model):

