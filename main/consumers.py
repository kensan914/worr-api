from abc import abstractmethod
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from channels.layers import get_channel_layer
from account.models import Account
from account.serializers import MeSerializer, UserSerializer
import fullfii
from main.serializers import NotificationSerializer
from main.models import Notification, NotificationType


class JWTAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = ''
        self.me = None

    async def connect(self):
        try:
            await self.accept()
        except Exception as e:
            raise

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await self.close()

    @abstractmethod
    async def set_group_name(self, _id):
        pass

    async def receive_auth(self, received_data):
        self.me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        await self.set_group_name(self.me.id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        user_data = await self.get_me_data(self.me)
        await self.send(text_data=json.dumps({
            'type': 'auth', 'profile': user_data,
        }))

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


class NotificationConsumer(JWTAsyncWebsocketConsumer):
    paginate_by = 10

    async def set_group_name(self, _id):
        self.group_name = 'notification_{}'.format(str(_id))

    async def receive_auth(self, received_data):
        self.me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        await self.set_group_name(self.me.id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        user_data = await self.get_me_data(self.me)

        await self.send(text_data=json.dumps({
            'type': 'auth', 'profile': user_data
        }))

    async def _receive(self, received_data):
        received_type = received_data['type']
        self.me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)

        if received_type == 'get':
            page = received_data['page']
            newest_notifications = Notification.objects.filter(recipient=self.me).exclude(
                type__in=[NotificationType.CANCEL_TALK_REQUEST]
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

            ### talk request ###  or  ### talk response ### or ### cancel talk request ###
            if notification.type == NotificationType.TALK_REQUEST or notification.type == NotificationType.TALK_RESPONSE or notification.type == NotificationType.CANCEL_TALK_REQUEST:
                room_id = event['reference_id']
                appended_data = { 'room_id': room_id }

            ### normal time ###
            else:
                appended_data = {}

            data = { 'type': 'notice', 'notification': notification_data }
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
    async def send_notification_async(cls, recipient, notification_type, subject=None, message='', reference_id=None):
        """
        ex) await NotificationConsumer.send_notification_async(recipient=self.target_user, subject=self.me, notification_type=NotificationType.TALK_RESPONSE, reference_id=self.room_id)
        """
        notification = await cls.create_notification(recipient, subject, notification_type, message)

        channel_layer = get_channel_layer()
        await channel_layer.group_send('notification_{}'.format(str(recipient.id)), {
            'type': 'notice',
            'notification_id': str(notification.id),
            'reference_id': str(reference_id) if reference_id is not None else None,
        })

    @classmethod
    def send_notification(cls, recipient, notification_type, subject=None, message='', reference_id=None):
        """
        ex) NotificationConsumer.send_notification(recipient=response_user, subject=request_user, notification_type=NotificationType.CANCEL_TALK_REQUEST, reference_id=room_id)
        """
        notification = async_to_sync(cls.create_notification)(recipient, subject, notification_type, message)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('notification_{}'.format(str(recipient.id)), {
            'type': 'notice',
            'notification_id': str(notification.id),
            'reference_id': str(reference_id) if reference_id is not None else None,
        })
