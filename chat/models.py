import uuid
from django.db import models
from django.utils import timezone


class Room(models.Model):
    def __str__(self):
        return '{} - {}'.format(self.request_user.username, self.response_user.username)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    is_start = models.BooleanField(verbose_name='開始状況', default=False)
    created_at = models.DateTimeField(verbose_name='作成時間', default=timezone.now)
    started_at = models.DateTimeField(verbose_name='トーク開始時間', null=True)
    request_user = models.ForeignKey('account.Account', verbose_name='リクエストユーザ', on_delete=models.CASCADE, related_name='request_room')
    response_user = models.ForeignKey('account.Account', verbose_name='レスポンスユーザ', on_delete=models.CASCADE, related_name='response_room')


class Message(models.Model):
    def __str__(self):
        return '{}({})'.format(str(self.room), self.time)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    room = models.ForeignKey(Room, verbose_name='チャットルーム', related_name='message', on_delete=models.CASCADE)
    content = models.TextField(verbose_name='メッセージ内容', max_length=1000, blank=True)
    time = models.DateTimeField(verbose_name='投稿時間', default=timezone.now)
    user = models.ForeignKey('account.Account', verbose_name='投稿者', on_delete=models.CASCADE)
    is_stored_on_request = models.BooleanField(verbose_name='リクエストユーザ側の保存状況', default=False)
    is_stored_on_response = models.BooleanField(verbose_name='レスポンスユーザ側の保存状況', default=False)
