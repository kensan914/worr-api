from django.utils import timezone
import fullfii
from chat.consumers import ChatConsumer
from chat.models import Room
from main.consumers import NotificationConsumer
from main.models import NotificationType


def manage_talking_time(end_minutes=1440, alert_minutes=1435):
    talking_rooms = Room.objects.filter(is_start=True, is_end=False)
    upd_talking_rooms = []
    for talking_room in talking_rooms:
        elapsed_seconds = (timezone.now() - talking_room.started_at).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # end talk
        if elapsed_minutes > end_minutes:
            talking_room.is_end = True
            talking_room.is_time_out = True
            talking_room.ended_at = timezone.now()
            upd_talking_rooms.append(talking_room)
            ChatConsumer.send_end_talk(talking_room.id, time_out=True)
            fullfii.change_status_of_talk(talking_room)
        # alert end talk
        elif elapsed_minutes > alert_minutes:
            if not talking_room.is_alert:
                talking_room.is_alert = True
                upd_talking_rooms.append(talking_room)
                ChatConsumer.send_end_talk(talking_room.id, alert=True)

    Room.objects.bulk_update(upd_talking_rooms, fields=['is_end', 'is_time_out', 'is_alert'])


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
        elapsed_seconds = (timezone.now() - not_started_room.created_at).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # close talk request
        if elapsed_minutes > close_minutes:
            NotificationConsumer.send_notification(recipient=not_started_room.request_user, subject=not_started_room.response_user,
                                                   notification_type=NotificationType.CANCEL_TALK_REQUEST_TO_REQ, reference_id=not_started_room.id)
            NotificationConsumer.send_notification(recipient=not_started_room.response_user, subject=not_started_room.request_user,
                                                   notification_type=NotificationType.CANCEL_TALK_REQUEST_TO_RES, reference_id=not_started_room.id)
            not_started_room.delete()
