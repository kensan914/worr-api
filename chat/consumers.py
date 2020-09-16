from channels.db import database_sync_to_async
import json
from main.consumers import JWTAsyncWebsocketConsumer, NotificationConsumer
from main.models import NotificationType
from .models import *
import fullfii


class ChatConsumer(JWTAsyncWebsocketConsumer):
    groups = ['broadcast']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = self.scope['url_route']['kwargs']['room_id'] if 'room_id' in self.scope['url_route']['kwargs'] else ''
        self.target_user = None
        self.room = None

    async def set_group_name(self, _id):
        self.group_name = 'room_{}'.format(str(_id))

    async def receive_auth(self, received_data):
        self.user = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        await self.set_group_name(self.room_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.set_room()

        @database_sync_to_async
        def get_room_request_user(room):
            return room.request_user
        self.target_user = await get_room_request_user(self.room)

        # set response notification to request user
        await self.channel_layer.group_send(self.group_name, {
            'type': 'notice_response',
            'user_id': str(self.user.id),
            'sender_channel_name': self.channel_name,
        })
        await NotificationConsumer.send_notification_async(recipient=self.target_user, subject=self.user, notification_type=NotificationType.CHAT_RESPONSE, reference_id=self.room_id)
        target_user_data = await self.get_user_data(self.target_user)

        await self.send(text_data=json.dumps({
            'type': 'auth', 'room_id': str(self.room_id), 'target_user': target_user_data,
        }))

    async def _receive(self, received_data):
        received_type = received_data['type']

        if received_type == 'chat_message':
            message_id = received_data['message_id']
            message = received_data['message']
            time = timezone.datetime.now()
            print(time)
            self.user = await fullfii.authenticate_jwt(received_data['token'], is_async=True)

            await self.create_message(received_data, time, self.user)
            await self.channel_layer.group_send(self.group_name, {
                    'type': 'chat_message',
                    'message_id': message_id,
                    'message': message,
                    'time': time.strftime('%Y/%m/%d %H:%M:%S'),
                    'sender_channel_name': self.channel_name,
            })

    async def chat_message(self, event):
        try:
            message_id = event['message_id']
            message = event['message']
            time = event['time']
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'room_id': str(self.room_id),
                'message_id': message_id,
                'message': message,
                'time': time,
                'me': event['sender_channel_name'] == self.channel_name,
            }))
        except Exception as e:
            raise

    async def notice_response(self, event):
        try:
            if event['sender_channel_name'] != self.channel_name:
                target_user = await self.get_user(user_id=event['user_id'])
                target_user_data = await self.get_user_data(user=target_user)
                await self.send(text_data=json.dumps({
                    'type': 'notice_response', 'room_id': str(self.room_id), 'target_user': target_user_data,
                }))
        except Exception as e:
            raise

    @database_sync_to_async
    def create_room(self, request_user, response_user):
        try:
            room = Room(
                id=self.room_id,
                request_user=request_user,
                response_user=response_user,
            )
            room.save()
            self.room = room
        except Exception as e:
            raise

    @database_sync_to_async
    def set_room(self):
        try:
            self.room = Room.objects.get(id=self.room_id)
        except Exception as e:
            raise

    @database_sync_to_async
    def create_message(self, message_data, time, user):
        try:
            room = Room.objects.get(
                id=self.room_id
            )
            Message.objects.create(
                room=room,
                id=message_data['message_id'],
                content=message_data['message'],
                time=time,
                user=user,
            )
        except Exception as e:
            raise


class ChatRequestConsumer(ChatConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = uuid.uuid4()
        self.target_user_id = self.scope['url_route']['kwargs']['user_id'] if 'user_id' in self.scope['url_route']['kwargs'] else ''

    async def receive_auth(self, received_data):
        self.user = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        await self.set_group_name(self.room_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        # create room
        self.target_user = await self.get_user(self.target_user_id)
        await self.create_room(request_user=self.user, response_user=self.target_user)

        # set notification to target user
        await NotificationConsumer.send_notification_async(recipient=self.target_user, subject=self.user, notification_type=NotificationType.CHAT_REQUEST, reference_id=self.room_id)
        target_user_data = await self.get_user_data(self.target_user)

        await self.send(text_data=json.dumps({
            'type': 'auth', 'room_id': str(self.room_id), 'target_user': target_user_data,
        }))
