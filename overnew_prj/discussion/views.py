from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from archive.models import Article
from account.notifications import notify, display_name
from .models import DiscussionRoom, DiscussionParticipant, Comment, CommentLike


def discussion_list(request):
    # 카테고리 탭별 기사 목록 (토론 가능한 기사들)
    articles = Article.objects.all().order_by("-created_at")
    return render(request, "discussion/discussion_list.html", {"articles": articles})


def room_select(request, article_id):
    # 실명/익명 방 선택 화면
    article = get_object_or_404(Article, pk=article_id)
    real_room, _ = DiscussionRoom.objects.get_or_create(article=article, room_type="real")
    anon_room, _ = DiscussionRoom.objects.get_or_create(article=article, room_type="anonymous")
    return render(request, "discussion/room_select.html", {
        "article": article,
        "real_room": real_room,
        "anon_room": anon_room,
    })


@login_required
def room_detail(request, article_id, room_type):
    article = get_object_or_404(Article, pk=article_id)
    room = get_object_or_404(DiscussionRoom, article=article, room_type=room_type)

    # 방 최초 입장 시 참여자로 등록
    participant, created = DiscussionParticipant.objects.get_or_create(
        room=room, user=request.user
    )
    if room.room_type == "anonymous" and participant.anon_number is None:
        # 입장 순서대로 익명 번호 부여
        current_count = DiscussionParticipant.objects.filter(
            room=room, anon_number__isnull=False
        ).count()
        participant.anon_number = current_count + 1
        participant.save()

    top_comments = (
        room.comments
        .filter(parent__isnull=True)
        .select_related("user")
        .prefetch_related("replies__user")
    )

    # 🌟 [수정] "이 방"에서의 유저별 익명 번호를 미리 계산해서 각 댓글에 붙여줌.
    # (기존 템플릿의 comment.user.discussionparticipant_set.first.anon_number 는
    #  유저가 참여한 "모든" 방 중 가장 먼저 참여한 기록을 가져와서, 다른 방(특히 실명방)
    #  참여 기록이 먼저 잡히면 anon_number가 None으로 나오는 버그가 있었음.)
    if room.room_type == "anonymous":
        anon_map = dict(
            DiscussionParticipant.objects.filter(room=room)
            .values_list("user_id", "anon_number")
        )
        for c in top_comments:
            c.anon_display = anon_map.get(c.user_id)
            for r in c.replies.all():
                r.anon_display = anon_map.get(r.user_id)

    return render(request, "discussion/room_detail.html", {
        "article": article,
        "room": room,
        "participant": participant,
        "top_comments": top_comments,
        "participant_count": room.participants.count(),
    })


@login_required
@require_POST
def create_comment(request, article_id, room_type):
    article = get_object_or_404(Article, pk=article_id)
    room = get_object_or_404(DiscussionRoom, article=article, room_type=room_type)

    content = request.POST.get("content", "").strip()
    parent_id = request.POST.get("parent_id")

    if not content:
        return JsonResponse({"error": "내용을 입력해주세요."}, status=400)

    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, room=room)

    comment = Comment.objects.create(
        room=room, user=request.user, parent=parent, content=content
    )

    if room.room_type == "anonymous":
        participant, _ = DiscussionParticipant.objects.get_or_create(room=room, user=request.user)
        shown_name = f"익명{participant.anon_number}" if participant.anon_number else "익명"
    else:
        shown_name = request.user.nickname or request.user.username

    # 🌟 내 댓글에 답글이 달리면 원댓글 작성자에게 알림 (익명방이면 누가 썼는지 숨김)
    if parent:
        is_anon = room.room_type == "anonymous"
        notify(
            recipient=parent.user,
            actor=request.user,
            notif_type="reply",
            text="내 댓글에 새 답글이 달렸어요" if is_anon
                 else f"{display_name(request.user)}님이 내 댓글에 답글을 남겼어요",
            link=f"/discussion/{article.pk}/{room.room_type}/",
            target_id=comment.id,
            anonymous=is_anon,
        )

    return JsonResponse({
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.strftime("%Y-%m-%d"),
        "parent_id": parent.id if parent else None,
        "display_name": shown_name,
        "room_type": room.room_type,
        "user_id": request.user.id,  # 🌟 추가: 프로필 링크 생성에 필요
    })



@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        # 🌟 내 댓글에 좋아요가 눌리면 알림 (익명방이면 누가 눌렀는지 숨김)
        is_anon = comment.room.room_type == "anonymous"
        notify(
            recipient=comment.user,
            actor=request.user,
            notif_type="comment_like",
            text="내 댓글에 좋아요가 눌렸어요" if is_anon
                 else f"{display_name(request.user)}님이 내 댓글을 좋아해요",
            link=f"/discussion/{comment.room.article_id}/{comment.room.room_type}/",
            target_id=comment.id,
            anonymous=is_anon,
        )

    return JsonResponse({
        "liked": liked,
        "like_count": comment.comment_likes.count(),
    })