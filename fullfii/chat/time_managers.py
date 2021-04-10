from chat.v2.consumers import ChatConsumerV2
from sys import version
from django.utils import timezone
import fullfii
from chat.consumers import ChatConsumer
from chat.models import MessageV2, TalkingRoom, Room
from main.consumers import NotificationConsumer
from main.models import NotificationType


def manage_talking_time(end_minutes, alert_minutes):
    talking_rooms = TalkingRoom.objects.filter(is_end=False)
    upd_talking_rooms = []
    exists_at_least_end_talk = False
    for talking_room in talking_rooms:
        # 最終メッセ―ジ(メッセージが無かったらroomの開始時間)
        messages = MessageV2.objects.filter(
            room=talking_room).order_by('-time')
        if messages.exists():
            last_message = messages.first()
            talking_room_time = last_message.time
        else:
            talking_room_time = talking_room.started_at

        elapsed_seconds = (
            timezone.now() - talking_room_time).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # end talk
        if elapsed_minutes > end_minutes:
            exists_at_least_end_talk = True

            fullfii.end_talk_v2(talking_room, ender=None, is_time_out=True)
            fullfii.end_talk_ticket(talking_room.speaker_ticket)
            fullfii.end_talk_ticket(talking_room.listener_ticket)

            # 通知
            fullfii.send_fcm(talking_room.speaker_ticket.owner, {
                'type': 'END_TALK',
                'user': talking_room.listener_ticket.owner
            })
            fullfii.send_fcm(talking_room.listener_ticket.owner, {
                'type': 'END_TALK',
                'user': talking_room.speaker_ticket.owner
            })

            # app内通知
            ChatConsumerV2.send_end_talk(
                room_id=talking_room.id, time_out=True)

        # alert end talk
        elif elapsed_minutes > alert_minutes:
            if not talking_room.is_alert:
                talking_room.is_alert = True
                upd_talking_rooms.append(talking_room)
                # 通知
                fullfii.send_fcm(talking_room.speaker_ticket.owner, {
                    'type': 'END_TALK_ALERT',
                })
                fullfii.send_fcm(talking_room.listener_ticket.owner, {
                    'type': 'END_TALK_ALERT',
                })
    TalkingRoom.objects.bulk_update(upd_talking_rooms, fields=[
        'is_end', 'is_time_out', 'is_alert'])

    if exists_at_least_end_talk:
        fullfii.start_matching(version=3)


def manage_after_talk_time(close_minutes=1440):
    end_rooms = Room.objects.filter(is_end=True)

    for end_room in end_rooms:
        elapsed_seconds = (timezone.now() - end_room.ended_at).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # close talk
        if elapsed_minutes > close_minutes:
            end_room.delete()


def manage_talk_request_time(close_minutes=1440):
    not_started_rooms = Room.objects.filter(is_start=False)

    for not_started_room in not_started_rooms:
        elapsed_seconds = (
            timezone.now() - not_started_room.created_at).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # close talk request
        if elapsed_minutes > close_minutes:
            NotificationConsumer.send_notification(
                recipient=not_started_room.request_user,
                subject=not_started_room.response_user,
                notification_type=NotificationType.CANCEL_TALK_REQUEST_TO_REQ,
                context={
                    'room_id': str(not_started_room.id),
                })
            NotificationConsumer.send_notification(
                recipient=not_started_room.response_user,
                subject=not_started_room.request_user,
                notification_type=NotificationType.CANCEL_TALK_REQUEST_TO_RES,
                context={
                    'room_id': str(not_started_room.id),
                })
            not_started_room.delete()
