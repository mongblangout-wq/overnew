from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime
from archive.models import Article


class DiscussionRoom(models.Model):
    ROOM_TYPE_CHOICES = [
        ("real", "실명토의방"),
        ("anonymous", "익명토의방"),
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="discussion_rooms")
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("article", "room_type")

    def __str__(self):
        return f"{self.article.title} - {self.get_room_type_display()}"

    @property
    def closes_at(self):
        # 기사 등록 시점부터 24시간 후 마감
        return self.article.created_at + datetime.timedelta(hours=24)

    @property
    def is_closed(self):
        return timezone.now() >= self.closes_at

    @property
    def time_left(self):
        remaining = self.closes_at - timezone.now()
        if remaining.total_seconds() <= 0:
            return None
        hours = int(remaining.total_seconds() // 3600)
        return hours


class DiscussionParticipant(models.Model):
    room = models.ForeignKey(DiscussionRoom, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    anon_number = models.PositiveIntegerField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user} in {self.room}"


class Comment(models.Model):
    room = models.ForeignKey(DiscussionRoom, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user} - {self.content[:20]}"


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="comment_likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")