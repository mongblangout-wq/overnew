from django.db import models
from django.conf import settings # NameError 해결을 위해 필수
import os
from uuid import uuid4
from django.utils import timezone


def upload_filepath(instance, filename):
    today_str=timezone.now().strftime("%Y%m%d")
    file_basename=os.path.basename(filename)
    return f'{instance._meta.model_name}/{today_str}/{str(uuid4())}_{file_basename}'


# 🌟 모델 이름 변경: account 앱의 NewsCategory와 충돌 방지
class ArchiveCategory(models.Model):
    nc_id = models.AutoField(primary_key=True)
    news_category = models.CharField(max_length=10)

    def __str__(self):
        return self.news_category


# 🌟 모델 이름 변경: account 앱의 Media와 충돌 방지
class ArchiveMedia(models.Model):
    media_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# User 참조 수정 (settings.AUTH_USER_MODEL 사용) 및 Category 참조 업데이트
class UserNews(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nc = models.ForeignKey(ArchiveCategory, on_delete=models.CASCADE) # 👈 이름 변경 반영

    class Meta:
        unique_together = ('user', 'nc')


# User 참조 수정 (settings.AUTH_USER_MODEL 사용) 및 Media 참조 업데이트
class UserMedia(models.Model):
    media = models.ForeignKey(ArchiveMedia, on_delete=models.CASCADE) # 👈 이름 변경 반영
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('media', 'user')


# Category/Media 참조 업데이트 및 related_name 명시
class Article(models.Model):
    article_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    news_content = models.TextField(blank=True)
    image = models.URLField(blank=True)
    view_count = models.PositiveIntegerField(default=0)   # ← 추가

    nc = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='archive_articles_by_cat'
    )
    media = models.ForeignKey(
        ArchiveMedia,
        on_delete=models.SET_NULL,
        null=True,
        related_name='archive_articles_by_media'
    )
    url = models.URLField(unique=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# User 참조 수정 (settings.AUTH_USER_MODEL 사용)
class Scrap(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    news = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')


class Like(models.Model):
    """유저가 기사에 '좋아요'를 누르는 것을 기록하는 모델"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    news = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 💡 유저 한 명이 한 기사에 한 번만 좋아요를 누를 수 있도록 설정
        unique_together = ('user', 'news')

    def __str__(self):
        return f"{self.user.username} likes {self.news.title[:20]}..."


# 🌟 [신규 추가] 북마크 모델 (스크랩과는 별개로, 상세페이지 북마크 버튼용)
class Bookmark(models.Model):
    """유저가 기사 상세페이지에서 '북마크' 버튼을 눌러 저장하는 것을 기록하는 모델"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    news = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.news.title[:20]}..."


# 🚨 NameError 해결 (User -> settings.AUTH_USER_MODEL)
class Discussion(models.Model):
    news = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # 👈 NameError 해결!
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('news', 'user')


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower} -> {self.following}"