from channels.db import DatabaseSyncToAsync
from django.db.models.query_utils import Q
from chat.models import MessageV2, TalkTicket, TalkingRoom
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import traceback


async def send_fcm(to_user, action):
    if not firebase_admin._apps:
        cred = credentials.Certificate(
            '/var/www/static/fullfii-firebase-adminsdk-cn02h-2e2b2efd56.json')
        firebase_admin.initialize_app(cred)

    registration_token = to_user.device_token
    if not registration_token:
        return

    fcm_reducer_result = await fcm_reducer(to_user, action)
    if fcm_reducer_result is None:
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=fcm_reducer_result['title'],
                body=fcm_reducer_result['body'],
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=fcm_reducer_result['badge'])
                )),
            token=registration_token,
        )

        try:
            response = messaging.send(message)
            print('Successfully sent message:', response)
        except:
            traceback.print_exc()
    except:
        traceback.print_exc()


async def fcm_reducer(to_user, action):
    result = {
        'title': '',
        'body': '',
        'badge': 0,
    }
    if action['type'] == 'SEND_MESSAGE':
        # action {type, user, message}
        if not action['user'].username or not action['message']:
            return
        result['title'] = ''
        result['body'] = '{}さん：{}'.format(
            action['user'].username, action['message']
        )
        result['badge'] = await fetch_total_unread_count(to_user)

    elif action['type'] == 'MATCH_TALK':
        # action {type, genreOfWorry}
        if not action['genreOfWorry'].label:
            return
        result['title'] = ''
        result['body'] = '【{}】新しい話し相手が見つかりました！'.format(
            action['genreOfWorry'].label)

    elif action['type'] == 'THUNKS':
        # action {type, user}
        if not action['user'].username:
            return
        result['title'] = ''
        result['body'] = '{}さんからありがとうをもらいました！'.format(action['user'].username)
    else:
        return

    return result


@DatabaseSyncToAsync
def fetch_total_unread_count(to_user):
    # fetch talking rooms
    talk_tickets = TalkTicket.objects.filter(owner=to_user, is_active=True)
    talking_rooms = TalkingRoom.objects.filter(is_end=False).filter(
        Q(speaker_ticket__in=talk_tickets) | Q(listener_ticket__in=talk_tickets))

    talking_room__ids = [talking_room.id for talking_room in talking_rooms]

    # fetch unread messages
    messages = MessageV2.objects.filter(room__id__in=talking_room__ids).filter(
        Q(is_stored_on_speaker=False) | Q(is_stored_on_listener=False)
    )

    return messages.count()
