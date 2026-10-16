#archive/urls.py
from django.urls import path
from . import views
app_name = "archive"

urlpatterns = [
    # API 엔드포인트
    path('api/article/preview', views.fetch_article_preview, name='api_article_preview'),
    path("articles/upload/", views.upload_article, name="upload_article"),
    path("users/<int:user_id>/scraps/", views.scrap_list, name="scrap_list"),
    path("users/<int:user_id>/bookmarks/", views.bookmark_list, name="bookmark_list"),  # 🌟 추가
    path("api/articles/<int:article_id>/", views.get_article_detail_api, name="api_article_detail"),
    path("api/articles/<int:article_id>/like/toggle/", views.toggle_like, name="api_toggle_like"),  # 🌟 추가
    path("api/articles/<int:article_id>/bookmark/toggle/", views.toggle_bookmark, name="api_toggle_bookmark"),  # 🌟 추가
    path("api/follow/toggle/", views.follow_toggle, name="api_follow_toggle"),
    path("api/users/<int:user_id>/following/", views.get_following_list, name="api_get_following_list"), # 🌟 추가
    path("api/users/<int:user_id>/followers/", views.get_followers_list, name="api_get_followers_list"),  # 🌟 추가
    path("api/users/search/", views.search_users, name="api_search_users"),

    # HTML
    path("", views.archive_main, name="home"),
    path("article/<int:article_id>/", views.article_detail, name="article_detail"),
    path("scrap/create/", views.create_scrap, name="create_scrap"),
    path("profile/<int:user_id>/", views.profile_detail, name="profile_detail"),


    # 기타
    path("ping/", views.ping, name="ping"),
]