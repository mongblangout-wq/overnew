import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # manage.py가 있는 폴더
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "overnew_prj.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from account.models import NewsCategory, UserNews
from archive.models import ArchiveCategory, ArchiveMedia, Article, Scrap, Follow

User = get_user_model()

username = os.environ["TEST_USERNAME"]
password = os.environ["TEST_PASSWORD"]

CATEGORIES = [
    ("politics", "정치"), ("economy", "경제"), ("society", "사회"),
    ("culture", "생활/문화"), ("it", "IT/과학"), ("world", "세계"),
    ("entertainment", "연예"), ("sports", "스포츠"),
]

for code, name in CATEGORIES:
    NewsCategory.objects.get_or_create(code=code, defaults={"name": name})
    ArchiveCategory.objects.get_or_create(news_category=name)

media, _ = ArchiveMedia.objects.get_or_create(name="연합뉴스")

# 카테고리마다 기사 2개, 조회수는 전부 다르게
views = 5000
for code, name in CATEGORIES:
    cat = ArchiveCategory.objects.get(news_category=name)
    for i in (1, 2):
        views -= 100
        Article.objects.get_or_create(
            url=f"https://example.com/ci-seed/{code}/{i}",
            defaults={
                "title": f"[{name}] CI 테스트 기사 {i}",
                "nc": cat,
                "media": media,
                "view_count": views,
            },
        )


def make_user(uname, nickname, pw, stance):
    user = User.objects.filter(username=uname).first()
    if user is None:
        user = User.objects.create_user(
            username=uname,
            password=pw,
            email=f"{uname}@example.com",
            nickname=nickname,
            age=25,
            gender="male",
            stance=stance,
        )
    else:
        # 이미 있는 계정도 매번 비밀번호를 현재 값으로 맞춤
        user.set_password(pw)
        user.save()
    return user


test_user = make_user(username, "ci-tester", password, "progressive")
other = make_user("ci_other", "ci-other", secrets.token_urlsafe(16), "conservative")

# 테스트 계정의 관심 카테고리: 경제
UserNews.objects.get_or_create(
    user=test_user, category=NewsCategory.objects.get(code="economy")
)

# feed/following 케이스용: 테스트 계정이 ci_other를 팔로우, ci_other가 기사 1개 스크랩
Follow.objects.get_or_create(follower=test_user, following=other)
economy_article = Article.objects.filter(nc__news_category="경제").first()
Scrap.objects.get_or_create(user=other, news=economy_article)

print(f"seed 완료: 기사 {Article.objects.count()}개, 유저 {User.objects.count()}명")