import traceback
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
import json
from abc import abstractmethod
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

from account.models import Account
from account.v4.serializers import MeSerializer, UserSerializer
from fullfii.lib.authSupport import authenticate_jwt


class JWTAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = ''
        self.me_id = None
        self.is_authenticated = False
        # Consumerは寿命が長いため, selfで管理する変数は競合に注意する. 例えばAccountオブジェクトをselfで管理したとし, 外部で
        # それが変更されたとき, 変更を反映することができない. 万が一Consumer内でsave()をしたら古い情報が上書き保存されてしまう.
        # selfで管理するものは一貫して不変のものに制限し, Modelオブジェクトは管理せず, 代わりにそのIDを管理し都度getする.

    async def connect(self):
        try:
            await self.accept()
        except Exception as e:
            traceback.print_exc()

    async def disconnect(self, close_code=None):
        await self._disconnect(close_code)
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        await self.close(close_code)

    @abstractmethod
    async def get_group_name(self, _id):
        return

    @abstractmethod
    async def _disconnect(self, close_code):
        pass  # receive other than auth

    @abstractmethod
    async def receive_auth(self, received_data):
        pass  # receive auth

    @abstractmethod
    async def _receive(self, received_data):
        pass  # receive other than auth

    async def receive(self, text_data):
        try:
            received_data = json.loads(text_data)

            # receive jwt token to authenticate
            if 'type' in received_data and received_data['type'] == 'auth':
                is_success = await self.receive_auth(received_data)
                if is_success:
                    self.is_authenticated = True
            else:
                if not self.is_authenticated:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Unauthorized error.'
                    }))
                    return
                await self._receive(received_data)

        except Exception as e:
            traceback.print_exc()

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return Account.objects.get(id=user_id)
        except Exception as e:
            traceback.print_exc()

    @database_sync_to_async
    def get_me_data(self, user):
        return MeSerializer(user).data

    @database_sync_to_async
    def get_user_data(self, user, isV2=False):
        return UserSerializer(user).data


class NotificationConsumer(JWTAsyncWebsocketConsumer):
    @classmethod
    def get_group_name(cls, _id):
        return 'notification_{}'.format(str(_id))

    async def _disconnect(self, close_code):
        pass  # 切断時特別な処理はしない

    async def receive_auth(self, received_data):
        """
        received_data: {'type': 'auth', 'token': token}

        return {
            'type': 'auth'
        }
        """

        me = await authenticate_jwt(received_data['token'], is_async=True)
        if me is None:
            # 401 Unauthorized
            # NotificationConsumerではgroupを作成するのにme_idを用いるため、この瞬間groupが未作成であるため。
            await self.close(4001)
            print('401 Unauthorized')
            return
        self.me_id = me.id

        self.group_name = self.get_group_name(self.me_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            'type': 'auth'
        }))
        return True

    async def _receive(self, received_data):
        pass  # 受信を受け付けない

    async def notice_talk(self, event):
        try:
            appended_data = event['context']
            data = {'type': 'notice_talk'}
            data.update(appended_data)
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            traceback.print_exc()

    @classmethod
    def send_notification_someone_participated(cls, owner_id, room_data, participant_id, should_start):
        group_name = cls.get_group_name(owner_id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'notice_talk',
            'context': {
                'status': 'SOMEONE_PARTICIPATED',
                'room': room_data,
                'participant_id': participant_id,
                'should_start': should_start
            }
        })
