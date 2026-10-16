from django.urls import path
from . import views

app_name = "discussion"

urlpatterns = [
    path("", views.discussion_list, name="community"),   # name 변경
    path("<int:article_id>/", views.room_select, name="room_select"),
    path("<int:article_id>/<str:room_type>/", views.room_detail, name="room_detail"),
    path("<int:article_id>/<str:room_type>/comment/", views.create_comment, name="create_comment"),
    path("comment/<int:comment_id>/like/", views.toggle_comment_like, name="toggle_comment_like"),
]