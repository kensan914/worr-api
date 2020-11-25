import uuid
from django.db import models
from django.utils import timezone


class Room(models.Model):
    def __str__(self):
        return '{} - {}'.format(self.request_user.username, self.response_user.username)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    request_user = models.ForeignKey('account.Account', verbose_name='リクエストユーザ', on_delete=models.CASCADE, related_name='request_room')
    response_user = models.ForeignKey('account.Account', verbose_name='レスポンスユーザ', on_delete=models.CASCADE, related_name='response_room')
    created_at = models.DateTimeField(verbose_name='作成時間', default=timezone.now)
    is_start = models.BooleanField(verbose_name='トーク開始状況', default=False)
    started_at = models.DateTimeField(verbose_name='トーク開始時間', null=True)
    is_alert = models.BooleanField(verbose_name='アラート済み', default=False)
    is_end = models.BooleanField(verbose_name='トーク終了状況', default=False)
    ended_at = models.DateTimeField(verbose_name='トーク終了時間', null=True)
    is_time_out = models.BooleanField(verbose_name='トーク終了理由(time out)', default=False)
    is_end_request = models.BooleanField(verbose_name='リクエストユーザ側のend状況', default=False)
    is_end_response = models.BooleanField(verbose_name='レスポンスユーザ側のend状況', default=False)
    is_closed_request = models.BooleanField(verbose_name='リクエストユーザ側のclose状況', default=False)
    is_closed_response = models.BooleanField(verbose_name='レスポンスユーザ側のclose状況', default=False)
    is_worried_request_user = models.BooleanField(verbose_name='リクエストユーザが相談者である', default=True)


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


class Worry(models.Model):
    class Meta:
        ordering = ['-time']

    def __str__(self):
        return '{}'.format(self.message)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    time = models.DateTimeField(verbose_name='投稿時間', default=timezone.now)
    message = models.TextField(verbose_name='メッセージ内容', max_length=280, blank=True)
    user = models.ForeignKey('account.Account', verbose_name='投稿者', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
