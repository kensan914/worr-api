import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import traceback


def send_fcm(to_user, action):
    if not firebase_admin._apps:
        cred = credentials.Certificate(
            '/var/www/static/fullfii-firebase-adminsdk-cn02h-2e2b2efd56.json')
        firebase_admin.initialize_app(cred)

    registration_token = to_user.device_token
    if not registration_token:
        return

    fcm_reducer_result = fcm_reducer(action)
    if fcm_reducer_result is None:
        return

    try:
        print(fcm_reducer_result['body'])
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
        print(message)

        try:
            response = messaging.send(message)
            print('Successfully sent message:', response)
        except:
            traceback.print_exc()
    except:
        traceback.print_exc()


def fcm_reducer(action):
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
        result['badge'] = 1

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
