from abc import abstractmethod
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from channels.layers import get_channel_layer
from account.models import Account, Status
from account.serializers import MeSerializer, UserSerializer
import fullfii
from main.serializers import NotificationSerializer
from main.models import Notification, NotificationType


class JWTAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = ''
        self.me_id = None
        # Consumerは寿命が長いため, selfで管理する変数は競合に注意する. 例えばAccountオブジェクトをselfで管理したとし, 外部で
        # それが変更されたとき, 変更を反映することができない. 万が一Consumer内でsave()をしたら古い情報が上書き保存されてしまう.
        # selfで管理するものは一貫して不変のものに制限し, Modelオブジェクトは管理せず, 代わりにそのIDを管理し都度getする.

    async def connect(self):
        try:
            await self.accept()
        except Exception as e:
            raise

    async def disconnect(self, close_code=None):
        await self._disconnect(close_code)
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await self.close(close_code)

    @abstractmethod
    async def get_group_name(self, _id):
        return

    async def _disconnect(self, close_code):
        pass # receive other than auth

    async def receive_auth(self, received_data):
        pass # receive auth

    async def _receive(self, received_data):
        pass # receive other than auth

    async def receive(self, text_data):
        try:
            received_data = json.loads(text_data)

            # receive jwt token to authenticate
            if 'type' in received_data and received_data['type'] == 'auth':
                await self.receive_auth(received_data)
            else:
                await self._receive(received_data)

        except Exception as e:
            raise

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return Account.objects.get(id=user_id)
        except Exception as e:
            raise

    @database_sync_to_async
    def get_me_data(self, user):
        return MeSerializer(user).data

    @database_sync_to_async
    def get_user_data(self, user):
        return UserSerializer(user).data

    @classmethod
    @database_sync_to_async
    def change_status(cls, me, status_val):
        if status_val in Status.values:
            me.status = status_val
            if status_val == Status.ONLINE:
                me.is_online = True
            elif status_val == Status.OFFLINE:
                me.is_online = False
            me.save()
            return me
        else:
            raise


class NotificationConsumer(JWTAsyncWebsocketConsumer):
    paginate_by = 10

    async def get_group_name(self, _id):
        return 'notification_{}'.format(str(_id))

    async def _disconnect(self, close_code):
        # change to offline
        if self.me_id:
            me = await self.get_user(self.me_id)
            await self.change_status(me, Status.OFFLINE)

    async def receive_auth(self, received_data):
        me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        if me is None:
            # 401 Unauthorized
            # NotificationConsumerではgroupを作成するのにme_idを用いるため、この瞬間groupが未作成であるため。
            await self.close(4001)
            print('401 Unauthorized')
            return
        self.me_id = me.id

        self.group_name = await self.get_group_name(self.me_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # change to online
        _me = await self.change_status(me, Status.ONLINE)
        me = _me if _me is not None else me
        user_data = await self.get_me_data(me)

        await self.send(text_data=json.dumps({
            'type': 'auth', 'profile': user_data
        }))

    async def _receive(self, received_data):
        received_type = received_data['type']
        me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)

        if received_type == 'get':
            page = received_data['page']
            newest_notifications = Notification.objects.filter(recipient=me).exclude(
                type__in=[NotificationType.CANCEL_TALK_REQUEST_TO_RES, NotificationType.CANCEL_TALK_REQUEST_TO_REQ]
            )[self.paginate_by * (page - 1): self.paginate_by * page]
            newest_notifications_data = await self.get_notification_data(newest_notifications, many=True)

            await self.send(text_data=json.dumps({
                'type': 'get', 'notifications': newest_notifications_data,
            }))

        elif received_type == 'read':
            notification_ids = received_data['notification_ids']
            await self.patch_notification_read(notification_ids)

            await self.send(text_data=json.dumps({
                'type': 'read', 'status': 'success',
            }))

    async def notice(self, event):
        try:
            notification_id = event['notification_id']

            notification = await self.get_notification(notification_id)
            notification_data = await self.get_notification_data(notification)

            ### talk request ###  or  ### talk response ###  or  ### cancel talk request ###  or  ### end talk ###
            if notification.type == NotificationType.TALK_REQUEST or notification.type == NotificationType.TALK_RESPONSE or\
                    notification.type == NotificationType.CANCEL_TALK_REQUEST_TO_RES or notification.type == NotificationType.CANCEL_TALK_REQUEST_TO_REQ:
                appended_data = event['context']
                # if 'room_id' in event['context']:
                #     appended_data.update({'room_id': event['context']['room_id']})
                # if 'worried_user_id' in event['context']:
                #     appended_data.update({'worried_user_id': event['context']['worried_user_id']})

            ### normal time ###
            else:
                appended_data = {}

            data = {'type': 'notice', 'notification': notification_data}
            data.update(appended_data)
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            raise

    @database_sync_to_async
    def get_notification(self, notification_id):
        try:
            return Notification.objects.get(id=notification_id)
        except Exception as e:
            raise

    @database_sync_to_async
    def get_notification_data(self, notification, many=False):
        return NotificationSerializer(notification, many=many).data

    @database_sync_to_async
    def patch_notification_read(self, notification_ids):
        try:
            upd_notifications = []
            for notification in Notification.objects.filter(id__in=notification_ids):
                notification.read = True
                upd_notifications.append(notification)
            Notification.objects.bulk_update(upd_notifications, fields=['read'])
        except Exception as e:
            raise

    @classmethod
    @database_sync_to_async
    def create_notification(cls, recipient, subject, notification_type, message):
        _notification = Notification(
            recipient=recipient,
            subject=subject,
            type=notification_type,
            message=message,
        )
        _notification.save()
        return _notification

    @classmethod
    async def send_notification_async(cls, recipient, notification_type, subject=None, message='', context=None):
        """
        ex) await NotificationConsumer.send_notification_async(recipient=self.target_user, subject=self.me, notification_type=NotificationType.TALK_RESPONSE, context={'room_id': str(self.room_id)})
        """
        notification = await cls.create_notification(recipient, subject, notification_type, message)

        channel_layer = get_channel_layer()
        await channel_layer.group_send('notification_{}'.format(str(recipient.id)), {
            'type': 'notice',
            'notification_id': str(notification.id),
            'context': context if context is not None else None,
        })

    @classmethod
    def send_notification(cls, recipient, notification_type, subject=None, message='', context=None):
        """
        ex) NotificationConsumer.send_notification(recipient=response_user, subject=request_user, notification_type=NotificationType.CANCEL_TALK_REQUEST_TO_RES, context={'room_id': str(room_id)})
        """
        notification = async_to_sync(cls.create_notification)(recipient, subject, notification_type, message)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('notification_{}'.format(str(recipient.id)), {
            'type': 'notice',
            'notification_id': str(notification.id),
            'context': context if context is not None else None,
        })
