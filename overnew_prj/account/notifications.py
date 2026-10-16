# account/notifications.py
import logging

from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


def display_name(user):
    return getattr(user, "nickname", None) or user.username


def notify(recipient, actor, notif_type, text, link="", target_id=None, anonymous=False):
    """
    recipient에게 알림을 만든다.

    - 자기 자신에게는 알림을 보내지 않음
    - anonymous=True 이면 누가 했는지(actor)를 DB에 저장하지 않음 (익명 토론방용)
    - 같은 (받는 사람, 행위자, 종류, 대상)의 알림이 이미 있으면 새로 만들지 않고
      "안 읽음"으로 되돌리고 최신 시간으로 갱신 (팔로우/언팔로우, 좋아요 취소/재클릭 연타 방지)
    - 알림 생성에 실패해도 원래 동작(팔로우, 댓글 등)은 막지 않음
    """
    if recipient is None or recipient == actor:
        return None

    stored_actor = None if anonymous else actor

    try:
        existing = Notification.objects.filter(
            recipient=recipient,
            actor=stored_actor,
            notif_type=notif_type,
            target_id=target_id,
        ).first()

        if existing:
            existing.text = text
            existing.link = link
            existing.is_read = False
            existing.created_at = timezone.now()
            existing.save(update_fields=["text", "link", "is_read", "created_at"])
            return existing

        return Notification.objects.create(
            recipient=recipient,
            actor=stored_actor,
            notif_type=notif_type,
            text=text,
            link=link,
            target_id=target_id,
        )
    except Exception:
        logger.exception("알림 생성 실패")
        return None