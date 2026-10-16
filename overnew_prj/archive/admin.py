from django.contrib import admin
from .models import ArchiveCategory, ArchiveMedia, Article, Scrap, Like, Discussion, Follow


@admin.register(ArchiveCategory)
class ArchiveCategoryAdmin(admin.ModelAdmin):
    list_display = ('nc_id', 'news_category')
    search_fields = ('news_category',)


@admin.register(ArchiveMedia)
class ArchiveMediaAdmin(admin.ModelAdmin):
    list_display = ('media_id', 'name')
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('article_id', 'title', 'nc', 'media', 'view_count', 'created_at')
    list_filter = ('nc', 'media')
    search_fields = ('title', 'url')
    ordering = ('-created_at',)


@admin.register(Scrap)
class ScrapAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'news', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__nickname', 'news__title')
    autocomplete_fields = ('user', 'news')
    ordering = ('-created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'news', 'created_at')
    search_fields = ('user__username', 'news__title')
    ordering = ('-created_at',)


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'news', 'created_at')
    search_fields = ('user__username', 'news__title')
    ordering = ('-created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__username', 'follower__nickname', 'following__username', 'following__nickname')
    autocomplete_fields = ('follower', 'following')
    ordering = ('-created_at',)