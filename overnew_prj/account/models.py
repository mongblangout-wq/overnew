# account/models.py (최종 수정본 - related_name 적용)
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
import os
from uuid import uuid4
from django.utils import timezone
from django.conf import settings # settings.AUTH_USER_MODEL을 사용하기 위해 필요

def upload_filepath(instance, filename):
    today_str=timezone.now().strftime("%Y%m%d")
    file_basename=os.path.basename(filename)
    return f'{instance._meta.model_name}/{today_str}/{str(uuid4())}_{file_basename}'

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("아이디(username)는 필수입니다.")
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)   # 해시 저장
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser는 is_staff=True 여야 합니다.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser는 is_superuser=True 여야 합니다.")

        return self.create_user(username, password, **extra_fields)


class NewsCategory(models.Model):
    """
    분야 테이블 (ERD의 nc_id 가 가리키는 대상)
    예: politics, economy ...
    """
    code = models.CharField(max_length=50, unique=True)  # 'politics' 등
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "news_category"

    def __str__(self):
        return self.name


class Media(models.Model):
    """
    언론사 테이블 (ERD의 media_id 가 가리키는 대상)
    예: kh, hani ...
    """
    code = models.CharField(max_length=50, unique=True)  # 'kh', 'hani' ...
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "media"

    def __str__(self):
        return self.name


class UserNews(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acc_usernews_set')
    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE, related_name='acc_category_set')

    class Meta:
        db_table = "user_news"
        unique_together = ("user", "category")


class UserMedia(models.Model):
    """
    유저가 선택한 언론사 (다대다)
    """
    # 🌟 related_name 추가: acc_usermedia_set
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acc_usermedia_set')
    media = models.ForeignKey(Media, on_delete=models.CASCADE)

    class Meta:
        db_table = "user_media"
        unique_together = ("user", "media")

class Notification(models.Model):
    """알림 (팔로우 / 내 댓글에 답글 / 내 댓글 좋아요)"""
    TYPE_FOLLOW = "follow"
    TYPE_REPLY = "reply"
    TYPE_COMMENT_LIKE = "comment_like"
    TYPE_CHOICES = [
        (TYPE_FOLLOW, "팔로우"),
        (TYPE_REPLY, "답글"),
        (TYPE_COMMENT_LIKE, "댓글 좋아요"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    # 익명방 알림은 누가 했는지 숨기기 위해 actor를 비워서 저장함
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="sent_notifications"
    )
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)      # 클릭 시 이동할 경로
    target_id = models.PositiveIntegerField(null=True, blank=True)  # 댓글 id 등 (중복 알림 방지용)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"[{self.notif_type}] -> {self.recipient} : {self.text}"