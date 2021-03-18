import random
import jwt
from asgiref.sync import sync_to_async
from rest_framework import exceptions
from account.models import Account
from rest_framework_jwt.utils import jwt_decode_handler
from chat.models import TalkTicket
from fullfii import start_matching, create_talk_ticket


def authenticate_jwt(jwt_token, is_async=False):
    """
    jwt_tokenを受け取り、userを返す
    __init__.pyには記述しない
    """
    @sync_to_async
    def get_user(_user_id):
        users = Account.objects.filter(id=_user_id)
        if users.exists():
            return users.first()
        return

    try:
        jwt_info = jwt_decode_handler(jwt_token)
        user_id = jwt_info.get('user_id')
        if is_async:
            user = get_user(user_id)
            # user = sync_to_async(Account.objects.get)(id=user_id)
        else:
            user = Account.objects.get(id=user_id)
        return user
    except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidSignatureError, KeyError, jwt.ExpiredSignatureError,):
        msg = "failed jwt authentication"
        raise exceptions.AuthenticationFailed(msg)


def on_signup_success(me):
    """
    signup成功時に実行. talk ticket作成 & start_matching()
    :param me:
    :return:
    """
    for worry in me.genre_of_worries.all():
        create_talk_ticket(me, worry)

    # sign up直後(デフォルト)は検索中断状態
    # start_matching()
