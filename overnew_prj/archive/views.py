# archive/views.py (AttributeError 해결을 위해 fetch_article_preview 재배치)

import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.db.models import Q, Count
from .utils import fetch_article_metadata
from account.notifications import notify, display_name

User = get_user_model()

# 🌟 user_id 대신 id 필드로 검색하도록 수정합니다.
def get_user_or_404(user_id: int):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError("존재하지 않는 사용자입니다.")


@csrf_exempt
@require_POST
def upload_article(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON 형식이 아닙니다."}, status=400)

    user_id = data.get("user_id")
    url = data.get("url")
    nc_id = data.get("nc_id")
    news_category = data.get("news_category")   # 🌟 추가: 한글 카테고리명으로도 조회 가능
    media_id = data.get("media_id")
    media_name = data.get("media_name")

    if not user_id or not url or (not nc_id and not news_category):
        return JsonResponse({"error": "user_id, url, nc_id(또는 news_category)는 필수입니다."}, status=400)

    try:
        ArchiveCategory = apps.get_model('archive', 'ArchiveCategory')
        ArchiveMedia = apps.get_model('archive', 'ArchiveMedia')
        Article = apps.get_model('archive', 'Article')
        Scrap = apps.get_model('archive', 'Scrap')
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    try:
        user = get_user_or_404(user_id)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)

    # 🌟 nc_id 우선, 없으면 news_category로 조회
    try:
        if nc_id:
            category = ArchiveCategory.objects.get(nc_id=nc_id)
        else:
            category = ArchiveCategory.objects.get(news_category=news_category)
    except ArchiveCategory.DoesNotExist:
        return JsonResponse({"error": "존재하지 않는 카테고리입니다."}, status=400)

    media = None
    if media_id:
        try:
            media = ArchiveMedia.objects.get(id=media_id)
        except ArchiveMedia.DoesNotExist:
            return JsonResponse({"error": "존재하지 않는 언론사입니다."}, status=400)
    elif media_name:
        media, _ = ArchiveMedia.objects.get_or_create(name=media_name)

    try:
        meta = fetch_article_metadata(url)
    except Exception as e:
        return JsonResponse({"error": f"메타데이터 수집 실패: {e}"}, status=500)

    article, created = Article.objects.get_or_create(
        url=url,
        defaults={
            "title": meta["title"],
            "summary": meta["summary"],
            "image": meta["image"],
            "nc": category,
            "media": media,
        },
    )

    Scrap.objects.get_or_create(user=user, news=article)

    return JsonResponse({
        "article_id": article.article_id,
        "title": article.title,
        "summary": article.summary,
        "image": article.image,
        "category": article.nc.news_category if article.nc else "",
        "media": article.media.name if article.media else "",
        "url": article.url,
        "created": created,
    })


# ------------------------------------------------------------------
# 🌟 [재배치] fetch_article_preview를 앞쪽 API 영역으로 이동 (오류 해결 목적)
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
def fetch_article_preview(request):
    """
    URL을 받아 메타데이터(제목, 이미지, 언론사 등)를 추출하여 반환합니다.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON 형식이 아닙니다."}, status=400)

    url = data.get("url")

    if not url:
        return JsonResponse({"error": "url은 필수입니다."}, status=400)

    # 1) 메타데이터 크롤링
    try:
        meta = fetch_article_metadata(url)
    except Exception as e:
        # 크롤링 실패 시 오류 메시지와 함께 빈 객체 반환
        print(f"Metadata fetch failed for {url}: {e}")
        return JsonResponse({"error": f"기사 정보를 가져오는 데 실패했습니다: {e}"}, status=500)

    # 2) 응답: 프론트엔드가 미리보기에 사용할 정보만 반환
    return JsonResponse({
        "title": meta.get("title", "제목 없음"),
        "summary": meta.get("summary", ""),
        "image": meta.get("image", ""),
        "url": url,
        "media_name_from_meta": meta.get("media_name", "출처 불명"),
    })
# ------------------------------------------------------------------


# --- 스크랩 리스트 API ---
@require_GET
def scrap_list(request, user_id: int):
    """
    GET /api/users/<user_id>/scraps/
    """
    try:
        Article = apps.get_model('archive', 'Article')
        Scrap = apps.get_model('archive', 'Scrap')
        User = get_user_model()
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "해당 사용자를 찾을 수 없습니다"}, status=404)

    qs = (
        Scrap.objects
        .filter(user=user)
        .select_related("news", "news__nc", "news__media")
        .annotate(like_count=Count("news__likes"))
        .order_by("-created_at")
    )

    data = [
        {
            "article_id": s.news.article_id,
            "title": s.news.title,
            "summary": s.news.summary,
            "image": s.news.image,
            "category": s.news.nc.news_category if s.news.nc else "",
            "media": s.news.media.name if s.news.media else "",
            "url": s.news.url,
            "views": s.news.view_count,
            "likes": s.like_count,
            "scraped_at": s.created_at.isoformat(),
        }
        for s in qs
    ]

    return JsonResponse(data, safe=False)


# 🌟 [신규 추가] 북마크 리스트 API (아카이브 메인의 '북마크' 탭용)
@require_GET
def bookmark_list(request, user_id: int):
    """
    GET /archive/users/<user_id>/bookmarks/
    """
    try:
        Bookmark = apps.get_model('archive', 'Bookmark')
        User = get_user_model()
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "해당 사용자를 찾을 수 없습니다"}, status=404)

    qs = (
        Bookmark.objects
        .filter(user=user)
        .select_related("news", "news__nc", "news__media")
        .annotate(like_count=Count("news__likes"))
        .order_by("-created_at")
    )

    data = [
        {
            "article_id": b.news.article_id,
            "title": b.news.title,
            "summary": b.news.summary,
            "image": b.news.image,
            "category": b.news.nc.news_category if b.news.nc else "",
            "media": b.news.media.name if b.news.media else "",
            "url": b.news.url,
            "views": b.news.view_count,
            "likes": b.like_count,
            "bookmarked_at": b.created_at.isoformat(),
        }
        for b in qs
    ]

    return JsonResponse(data, safe=False)


# 🌟 [신규 추가] 좋아요 토글 API (기사 상세페이지 플로팅 버튼용)
@login_required
@require_POST
def toggle_like(request, article_id: int):
    """
    POST /archive/api/articles/<article_id>/like/toggle/
    """
    try:
        Article = apps.get_model('archive', 'Article')
        Like = apps.get_model('archive', 'Like')
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    article = get_object_or_404(Article, article_id=article_id)

    like, created = Like.objects.get_or_create(user=request.user, news=article)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    like_count = Like.objects.filter(news=article).count()

    return JsonResponse({"liked": liked, "like_count": like_count})


# 🌟 [신규 추가] 북마크 토글 API (기사 상세페이지 플로팅 버튼용)
@login_required
@require_POST
def toggle_bookmark(request, article_id: int):
    """
    POST /archive/api/articles/<article_id>/bookmark/toggle/
    """
    try:
        Article = apps.get_model('archive', 'Article')
        Bookmark = apps.get_model('archive', 'Bookmark')
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    article = get_object_or_404(Article, article_id=article_id)

    bookmark, created = Bookmark.objects.get_or_create(user=request.user, news=article)
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True

    return JsonResponse({"bookmarked": bookmarked})


# 🌟 추가: Article ID로 상세 정보 조회 API
@require_GET
def get_article_detail_api(request, article_id: int):
    """
    GET /archive/api/articles/<article_id>/
    article_id를 받아 해당 기사의 상세 정보(iframe용 url 포함)를 반환합니다.
    """
    try:
        Article = apps.get_model('archive', 'Article')
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    # Article 객체를 가져옵니다.
    article = get_object_or_404(Article, article_id=article_id)

    return JsonResponse({
        "article_id": article.article_id,
        "title": article.title,
        "url": article.url, # 👈 iframe에 사용할 핵심 정보
    })


def ping(request):
    return HttpResponse("archive API OK")

def archive_main(request):
    if not request.user.is_authenticated:
        return redirect('account:login')

    user = request.user

    try:
        Follow = apps.get_model('archive', 'Follow')
        followers_count = Follow.objects.filter(following=user).count()
    except LookupError:
        followers_count = 0

    topics = list(user.acc_usernews_set.values_list('category__code', flat=True))

    context = {
        'current_user_id': user.id,
        'current_user_nickname': user.nickname if hasattr(user, 'nickname') else user.username,
        'current_user_topics': topics,
        'current_user_followers': followers_count,
    }
    return render(request, "archive/archive.html", context)


# 🌟 [수정] 좋아요/북마크 초기 상태와 좋아요 수를 템플릿에 전달
def article_detail(request, article_id):
    Article = apps.get_model('archive', 'Article')
    Like = apps.get_model('archive', 'Like')
    Bookmark = apps.get_model('archive', 'Bookmark')

    article = get_object_or_404(Article, article_id=article_id)

    is_liked = False
    is_bookmarked = False
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, news=article).exists()
        is_bookmarked = Bookmark.objects.filter(user=request.user, news=article).exists()

    like_count = Like.objects.filter(news=article).count()

    return render(request, "archive/article-detail.html", {
        "article": article,
        "is_liked": is_liked,
        "is_bookmarked": is_bookmarked,
        "like_count": like_count,
    })


@login_required
def create_scrap(request):
    return render(request, "archive/create-scrap.html", {"current_user_id": request.user.id})

def profile_detail(request, user_id):
    if not request.user.is_authenticated:
        return redirect('account:login')

    target = get_object_or_404(User, id=user_id)

    Follow = apps.get_model('archive', 'Follow')
    is_following = Follow.objects.filter(follower=request.user, following=target).exists()
    followers_count = Follow.objects.filter(following=target).count()
    topics = list(target.acc_usernews_set.values_list('category__code', flat=True))

    context = {
        'current_user_id': request.user.id,
        'target_user_id': target.id,
        'target_nickname': target.nickname,
        'target_topics': topics,
        # 템플릿의 <script type="application/json"> 안에 들어가므로 '<'는 이스케이프
        'target_topics_json': json.dumps(topics, ensure_ascii=False).replace("<", "\\u003c"),
        'target_followers': followers_count,
        'is_following': is_following,
    }
    return render(request, "archive/profile-detail.html", context)


# 🌟 추가: 팔로우/언팔로우 처리 API
@csrf_exempt
@require_POST
def follow_toggle(request):
    """
    POST /archive/api/follow/toggle/
    팔로우 관계를 생성하거나 삭제(토글)합니다.
    요청 데이터: { "follower_id": 1, "following_id": 2 }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON 형식이 아닙니다."}, status=400)

    follower_id = data.get("follower_id")
    following_id = data.get("following_id")

    if not follower_id or not following_id:
        return JsonResponse({"error": "follower_id와 following_id는 필수입니다."}, status=400)

    try:
        # Follow 모델이 archive 앱에 있다고 가정합니다.
        Follow = apps.get_model('archive', 'Follow')
        User = get_user_model()
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    try:
        follower = User.objects.get(id=follower_id)
        following = User.objects.get(id=following_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "사용자를 찾을 수 없습니다."}, status=404)

    if follower.id == following.id:
        return JsonResponse({"error": "자기 자신을 팔로우할 수 없습니다."}, status=400)

    # 팔로우 관계 확인 및 토글
    follow_relation, created = Follow.objects.get_or_create(
        follower=follower,
        following=following
    )

    if not created:
        # 이미 존재하면 삭제 (언팔로우)
        follow_relation.delete()
        return JsonResponse({"status": "unfollowed", "message": "언팔로우했습니다."})
    else:
        # 새로 생성됨 (팔로우) → 팔로우 당한 사람에게 알림
        notify(
            recipient=following,
            actor=follower,
            notif_type="follow",
            text=f"{display_name(follower)}님이 회원님을 팔로우했어요",
            link=f"/archive/profile/{follower.id}/",
        )
        return JsonResponse({"status": "followed", "message": "팔로우했습니다."})


# 🌟 추가: 특정 사용자의 팔로잉 목록 조회 API
@require_GET
def get_following_list(request, user_id: int):
    """
    GET /archive/api/users/<user_id>/following/
    특정 사용자가 팔로우하는 사용자 목록을 반환합니다.
    """
    try:
        Follow = apps.get_model('archive', 'Follow')
        User = get_user_model()
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    try:
        # 1. 대상 사용자 객체 조회
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "사용자를 찾을 수 없습니다."}, status=404)

    # 2. 해당 사용자가 팔로우하는 관계만 필터링 (follower=target_user)
    following_qs = Follow.objects.filter(follower=target_user).select_related('following')

    following_data = []
    for relation in following_qs:
        followed_user = relation.following

        following_data.append({
            "id": followed_user.id,
            "nickname": followed_user.nickname,
            "tags": ["IT/과학", "문화"], # 임시 데이터 (실제 데이터 연동 필요)
            "avatar": "/static/image/avatar-placeholder.png",
        })

    return JsonResponse(following_data, safe=False)

# 🌟 추가: 특정 사용자를 팔로우하는 사람(팔로워) 목록 조회 API
@login_required
@require_GET
def get_followers_list(request, user_id: int):
    """
    GET /archive/api/users/<user_id>/followers/
    해당 사용자를 팔로우하는 사용자 목록 + 내가 그 사람을 팔로우 중인지 여부를 반환합니다.
    """
    Follow = apps.get_model('archive', 'Follow')
    target = get_object_or_404(User, id=user_id)

    relations = (
        Follow.objects
        .filter(following=target)
        .select_related('follower')
        .prefetch_related('follower__acc_usernews_set__category')
        .order_by('-created_at')
    )

    my_following_ids = set(
        Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    )

    data = []
    for rel in relations:
        f = rel.follower
        data.append({
            "id": f.id,
            "nickname": f.nickname or f.username,
            "tags": [un.category.name for un in f.acc_usernews_set.all()],
            "avatar": "/static/image/avatar-placeholder.png",
            "isFollowing": f.id in my_following_ids,
            "isMe": f.id == request.user.id,
        })

    return JsonResponse(data, safe=False)


@login_required
@require_GET
def search_users(request):
    """
    GET /archive/api/users/search/?q=검색어
    닉네임 또는 아이디로 유저를 검색하고, 본인의 팔로우 여부를 함께 반환합니다.
    """
    try:
        Follow = apps.get_model('archive', 'Follow')
    except LookupError as e:
        return JsonResponse({"error": f"모델 로드 실패: {e}"}, status=500)

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    users_qs = User.objects.filter(
        Q(nickname__icontains=query) | Q(username__icontains=query)
    ).exclude(pk=request.user.pk)[:30]

    following_ids = set(
        Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    )

    data = [
        {
            "id": u.id,
            "nickname": u.nickname,
            "tags": [],
            "avatar": "/static/image/avatar-placeholder.png",
            "isFollowing": u.id in following_ids,
        }
        for u in users_qs
    ]
    return JsonResponse(data, safe=False)