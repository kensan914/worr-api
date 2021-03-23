from channels.db import DatabaseSyncToAsync
from django.db.models.query_utils import Q
from chat.models import MessageV2, TalkStatus, TalkTicket, TalkingRoom
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
        badge_apns = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(badge=fcm_reducer_result['badge'])
            )) if fcm_reducer_result['badge'] > 0 else None

        message = messaging.Message(
            notification=messaging.Notification(
                title=fcm_reducer_result['title'],
                body=fcm_reducer_result['body'],
            ),
            apns=badge_apns,
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
        # action {type, user, message, receiver_talk_ticket}
        if action['receiver_talk_ticket'].status == TalkStatus.APPROVING:
            # 相手方がトークを承認してなかった時, SEND_MESSAGE通知を送らない
            return
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
    total_unread_count = 0
    talk_tickets = TalkTicket.objects.filter(owner=to_user, is_active=True)

    for talk_ticket in talk_tickets:
        is_speaker = talk_ticket.is_speaker

        # fetch talking room
        talking_rooms = TalkingRoom.objects.filter(is_end=False).filter(
            Q(speaker_ticket=talk_ticket) | Q(listener_ticket=talk_ticket))
        if not talking_rooms.exists():
            continue
        talking_room = talking_rooms.first()

        # fetch unread messages
        if is_speaker:
            messages = MessageV2.objects.filter(
                room__id=talking_room.id).filter(is_read_speaker=False)
        else:
            messages = MessageV2.objects.filter(
                room__id=talking_room.id).filter(is_read_listener=False)

        total_unread_count += messages.count()

    return total_unread_count
