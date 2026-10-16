from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse

from archive.models import Article, Scrap
from archive.models import Article, Scrap, Follow


def feed(request):
    articles = (
        Article.objects
        .annotate(like_count=Count('likes'))
        .order_by('-created_at')
    )
    return render(request, 'feed/feed.html', {
        'mode': 'all',
        'articles': articles,
    })


TOPIC_TO_CATEGORY_NAME = {
    'politics': '정치',
    'economy': '경제',
    'society': '사회',
    'culture': '생활/문화',
    'it': 'IT/과학',
    'world': '세계',
    'enter': '연예',
    'sport': '스포츠',
}


def _serialize_article(a):
    return {
        "id": a.article_id,
        "category": a.nc.news_category if a.nc else "",
        "source": a.media.name if a.media else "",
        "title": a.title,
        "views": a.view_count,
        "likes": getattr(a, 'like_count', 0),
        "time": a.created_at.strftime('%Y-%m-%d %H:%M'),
        "image": a.image or "",
    }


def hot_feed_api(request):
    topic = request.GET.get('topic')

    qs = (
        Article.objects
        .select_related('media', 'nc')
        .annotate(like_count=Count('likes'))
        .order_by('-view_count', '-like_count', '-created_at')
    )

    if topic:
        category_name = TOPIC_TO_CATEGORY_NAME.get(topic)
        if category_name:
            qs = qs.filter(nc__news_category=category_name)

    qs = qs[:20]
    return JsonResponse({"articles": [_serialize_article(a) for a in qs]})



@login_required
def following_feed_api(request):
    topic = request.GET.get('topic')
    category_name = TOPIC_TO_CATEGORY_NAME.get(topic)

    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)

    scraps = (
        Scrap.objects
        .select_related('user', 'news', 'news__media', 'news__nc')
        .filter(user_id__in=following_ids)
        .order_by('-created_at')
    )

    if category_name:
        scraps = scraps.filter(news__nc__news_category=category_name)

    results = []
    for s in scraps:
        u = s.user
        a = s.news
        results.append({
            "user": {"id": u.id, "nickname": u.nickname or u.username},
            "article": {
                "id": a.article_id,
                "category": a.nc.news_category if a.nc else "",
                "source": a.media.name if a.media else "",
                "title": a.title,
                "views": a.view_count,
                "time": a.created_at.strftime('%Y-%m-%d %H:%M'),
                "image": a.image or "",
            }
        })

    return JsonResponse({"requires_login": False, "results": results})