import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging


def send_fcm(to_user, action):
    print('start send_fcm')
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

    message = messaging.Message(
        notification=messaging.Notification(
            title=fcm_reducer_result['title'],
            body=fcm_reducer_result['body'],
        ),
        token=registration_token,
    )
    print(fcm_reducer_result)

    response = messaging.send(message)
    print('Successfully sent message:', response)


def fcm_reducer(action):
    result = {
        'title': '',
        'body': '',
    }
    if action['type'] == 'SEND_MESSAGE':
        # action {type, user, message}
        if not action['user'].username or not action['message']:
            return
        result['title'] = ''
        result['body'] = '{}さん：{}'.format(
            action['user'].username, action['message'])
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
