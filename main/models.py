import uuid
from django.db import models
from django.utils import timezone
from account.models import ParamsModel


class NotificationType(models.TextChoices):
    TALK_REQUEST = 'talk_request', 'トークリクエスト'
    TALK_RESPONSE = 'talk_response', 'トークレスポンス'
    CANCEL_TALK_REQUEST_TO_RES = 'cancel_talk_request_to_res', 'レスポンスユーザへのトークリクエストのキャンセル'
    CANCEL_TALK_REQUEST_TO_REQ = 'cancel_talk_request_to_req', 'リクエストユーザへのトークリクエストのキャンセル'


class Notification(models.Model):
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return str(self.date)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey('account.Account', verbose_name='受取人', on_delete=models.CASCADE, related_name='recipient_notification')
    subject = models.ForeignKey('account.Account', verbose_name='主語', null=True, on_delete=models.CASCADE, related_name='subject_notification')
    type = models.CharField(verbose_name='タイプ', max_length=40, choices=NotificationType.choices, default=NotificationType.TALK_REQUEST)
    message = models.CharField(verbose_name='メッセージ', max_length=250, blank=True)
    read = models.BooleanField(verbose_name='既読', default=False)
    date = models.DateTimeField(verbose_name='登録日', default=timezone.now)
