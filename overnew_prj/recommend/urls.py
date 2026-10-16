# recommend/urls.py

from django.urls import path
from .views import *

app_name = "recommend"

urlpatterns = [
    path('api/recommend/', RecommendUserView.as_view(), name='api_recommend_list'),
    path('', recommend_main, name='main'),   # 'main/' → '' 로, name도 'main'으로 변경
    path('api/articles/', recommend_article_api, name='api_articles'),
]