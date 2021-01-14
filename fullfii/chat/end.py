from django.db.models import Q
from django.utils import timezone
from account.models import Status
from chat.models import Room


def end_talk_v2(room):
    """
    v2. トークを終了するときに1回だけ実行. set talked_accounts.
    :param room:
    :return:
    """
    room.is_end = True
    room.ended_at = timezone.now()
    room.save()

    speaker = room.speaker_ticket.owner
    listener = room.listener_ticket.owner
    speaker.talked_accounts.add(listener)
    speaker.save()
    listener.talked_accounts.add(speaker)
    listener.save()


def end_talk(room, is_first_time, user):
    """
    トークを終了するときにリクエストユーザ、レスポンスユーザで2回実行. roomレコードの変更
    :param room:
    :param is_first_time: 初めてならTrue. 既にroomのend処理がなされていたらFalse
    :param user
    :return:
    """
    # end talk for the first time
    if is_first_time:
        room.is_end = True
        room.ended_at = timezone.now()

    # turn on is_end_(req or res)
    if user.id == room.request_user.id:
        room.is_end_request = True
    else:
        room.is_end_response = True
    room.save()


def change_status_of_talk(room, user_id=None):
    """
    トークを終了するときに一度だけ実行. ユーザのstatusを変更
    :param room:
    :param user_id:
    :return:
    """
    room_members = [room.request_user, room.response_user]
    me = None

    for user in room_members:
        talking_rooms = Room.objects.exclude(id=room.id).filter(Q(request_user__id=user.id) | Q(response_user_id=user.id), is_start=True, is_end=False)
        if not talking_rooms.exists():
            if user.is_online:
                user.status = Status.ONLINE
            else:
                user.status = Status.OFFLINE
            user.save()
            if user_id is not None and user.id == user_id:
                me = user

    if me is not None:
        return me
