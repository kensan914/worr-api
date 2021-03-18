import uuid
from django.db import models
from django.utils import timezone


class TalkStatus(models.TextChoices):
    TALKING = 'talking', '会話中'
    WAITING = 'waiting', '待機中'
    STOPPING = 'stopping', '停止中'
    FINISHING = 'finishing', '終了中'


class TalkTicket(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'トークチケット'
        unique_together = ('owner', 'worry')

    def __str__(self):
        alert_msg = '【削除】 ' if not self.is_active else ''
        return '{}{}-{}-{}'.format(alert_msg, self.owner.username, self.worry.label, self.status)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner = models.ForeignKey(
        'account.Account', verbose_name='所持者', on_delete=models.CASCADE)
    worry = models.ForeignKey('account.GenreOfWorries',
                              verbose_name='悩み', on_delete=models.CASCADE)
    is_speaker = models.BooleanField(verbose_name='話し手希望', default=True)
    status = models.CharField(verbose_name='状態', max_length=100,
                              choices=TalkStatus.choices, default=TalkStatus.STOPPING)
    wait_start_time = models.DateTimeField(
        verbose_name='待機開始時間', default=timezone.now)

    can_talk_heterosexual = models.BooleanField(
        verbose_name='異性との相談を許可', default=True)
    can_talk_different_job = models.BooleanField(
        verbose_name='異職業との相談を許可', default=True)
    is_active = models.BooleanField(verbose_name='アクティブ状態', default=True)


class TalkingRoom(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'ルーム'
        ordering = ['-started_at']

    def __str__(self):
        alert_msg = '【終了】 ' if self.is_end else ''
        return '{}{} - {}({})'.format(alert_msg, self.speaker_ticket.owner.username, self.listener_ticket.owner.username, self.speaker_ticket.worry.label)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    speaker_ticket = models.ForeignKey('chat.TalkTicket', verbose_name='話し手talkTicket',
                                       on_delete=models.CASCADE, related_name='speaker_ticket_talking_room', null=True)
    listener_ticket = models.ForeignKey('chat.TalkTicket', verbose_name='聞き手talkTicket',
                                        on_delete=models.CASCADE, related_name='listener_ticket_talking_room', null=True)
    started_at = models.DateTimeField(
        verbose_name='トーク開始時間', default=timezone.now)
    is_alert = models.BooleanField(verbose_name='アラート済み', default=False)
    is_end = models.BooleanField(verbose_name='トーク終了状況', default=False)
    ended_at = models.DateTimeField(verbose_name='トーク終了時間', null=True)
    is_time_out = models.BooleanField(
        verbose_name='トーク終了理由(time out)', default=False)


class MessageV2(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'メッセージ'
        ordering = ['-time']

    def __str__(self):
        return '{}({})'.format(str(self.room), self.time)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    room = models.ForeignKey(TalkingRoom, verbose_name='チャットルーム',
                             related_name='message', on_delete=models.CASCADE)
    content = models.TextField(
        verbose_name='メッセージ内容', max_length=1000, blank=True)
    time = models.DateTimeField(verbose_name='投稿時間', default=timezone.now)
    user = models.ForeignKey(
        'account.Account', verbose_name='投稿者', on_delete=models.CASCADE)
    is_stored_on_speaker = models.BooleanField(
        verbose_name='話し手側の保存状況', default=False
    )
    is_stored_on_listener = models.BooleanField(
        verbose_name='聞き手側の保存状況', default=False
    )
    is_read_speaker = models.BooleanField(
        verbose_name='話し手側の既読状況', default=False
    )
    is_read_listener = models.BooleanField(
        verbose_name='聞き手側の既読状況', default=False
    )


# only use v1
class Room(models.Model):
    def __str__(self):
        return '{} - {}'.format(self.request_user.username, self.response_user.username)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    request_user = models.ForeignKey(
        'account.Account', verbose_name='リクエストユーザ', on_delete=models.CASCADE, related_name='request_room')
    response_user = models.ForeignKey(
        'account.Account', verbose_name='レスポンスユーザ', on_delete=models.CASCADE, related_name='response_room')
    created_at = models.DateTimeField(
        verbose_name='作成時間', default=timezone.now)
    is_start = models.BooleanField(verbose_name='トーク開始状況', default=False)
    started_at = models.DateTimeField(verbose_name='トーク開始時間', null=True)
    is_alert = models.BooleanField(verbose_name='アラート済み', default=False)
    is_end = models.BooleanField(verbose_name='トーク終了状況', default=False)
    ended_at = models.DateTimeField(verbose_name='トーク終了時間', null=True)
    is_time_out = models.BooleanField(
        verbose_name='トーク終了理由(time out)', default=False)
    is_end_request = models.BooleanField(
        verbose_name='リクエストユーザ側のend状況', default=False)
    is_end_response = models.BooleanField(
        verbose_name='レスポンスユーザ側のend状況', default=False)
    is_closed_request = models.BooleanField(
        verbose_name='リクエストユーザ側のclose状況', default=False)
    is_closed_response = models.BooleanField(
        verbose_name='レスポンスユーザ側のclose状況', default=False)
    is_worried_request_user = models.BooleanField(
        verbose_name='リクエストユーザが相談者である', default=True)


# only use v1
class Message(models.Model):
    def __str__(self):
        return '{}({})'.format(str(self.room), self.time)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    room = models.ForeignKey(Room, verbose_name='チャットルーム',
                             related_name='message', on_delete=models.CASCADE)
    content = models.TextField(
        verbose_name='メッセージ内容', max_length=1000, blank=True)
    time = models.DateTimeField(verbose_name='投稿時間', default=timezone.now)
    user = models.ForeignKey(
        'account.Account', verbose_name='投稿者', on_delete=models.CASCADE)
    is_stored_on_request = models.BooleanField(
        verbose_name='リクエストユーザ側の保存状況', default=False)
    is_stored_on_response = models.BooleanField(
        verbose_name='レスポンスユーザ側の保存状況', default=False)


# only use v1
class Worry(models.Model):
    class Meta:
        ordering = ['-time']

    def __str__(self):
        return '{}'.format(self.message)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    time = models.DateTimeField(verbose_name='投稿時間', default=timezone.now)
    message = models.TextField(
        verbose_name='メッセージ内容', max_length=280, blank=True)
    user = models.ForeignKey(
        'account.Account', verbose_name='投稿者', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
