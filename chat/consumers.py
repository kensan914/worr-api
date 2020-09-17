from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
import json

from chat.serializers import MessageSerializer
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
        self.is_request_user = True

    async def set_group_name(self, _id):
        self.group_name = 'room_{}'.format(str(_id))

    async def receive_auth(self, received_data):
        self.me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        await self.set_group_name(self.room_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        result = await self.get_room()
        if result:
            self.room = result
        else:
            await self.close()
            return

        room_users = await self.get_room_users(self.room)
        if room_users['request_user'].id == self.me.id: # if I'm request user
            self.is_request_user = True
            self.target_user = room_users['response_user']
        elif room_users['response_user'].id == self.me.id: # if I'm response user
            self.is_request_user = False
            self.target_user = room_users['request_user']
            # If init is true, set response notification to request user
            if received_data['init']:
                await NotificationConsumer.send_notification_async(recipient=self.target_user, subject=self.me, notification_type=NotificationType.TALK_RESPONSE, reference_id=self.room_id)
        else:
            raise

        target_user_data = await self.get_user_data(user=self.target_user)

        await self.send(text_data=json.dumps({
            'type': 'auth', 'room_id': str(self.room_id), 'target_user': target_user_data,
        }))

        # Send messages that you haven't stored yet
        not_stored_messages_data = await self.get_not_stored_messages_data(self.room, self.is_request_user, self.me)
        if not_stored_messages_data:
            await self.send(text_data=json.dumps({
                'type': 'multi_chat_messages',
                'room_id': str(self.room_id),
                'messages': not_stored_messages_data,
            }))

    async def _receive(self, received_data):
        received_type = received_data['type']

        if received_type == 'chat_message':
            message_id = received_data['message_id']
            message = received_data['message']
            time = timezone.datetime.now()

            self.me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)

            await self.create_message(received_data, time, self.me)
            await self.channel_layer.group_send(self.group_name, {
                    'type': 'chat_message',
                    'message_id': message_id,
                    'message': message,
                    'time': time.strftime('%Y/%m/%d %H:%M:%S'),
                    'sender_channel_name': self.channel_name,
            })

        elif received_type == 'store':
            message_id = received_data['message_id']
            self.me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
            await self.turn_on_message_stored(self.is_request_user, message_id=message_id)

        elif received_type == 'store_by_room':
            await self.turn_on_message_stored(self.is_request_user, room_id=self.room_id)

    async def chat_message(self, event):
        try:
            message_id = event['message_id']
            message = event['message']
            time = event['time']
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'room_id': str(self.room_id),
                'message': {
                    'message_id': message_id,
                    'message': message,
                    'is_me': event['sender_channel_name'] == self.channel_name,
                    'time': time,
                },
            }))
        except Exception as e:
            raise

    @database_sync_to_async
    def get_room(self):
        rooms = Room.objects.filter(id=self.room_id)
        if rooms.count() == 1:
            return rooms.first()
        elif rooms.count() == 0:
            async_to_sync(self.send)(text_data=json.dumps({
                'type': 'error',
                'error_type': 'not_found_room',
                'message': 'お探しのトークルームは見つかりませんでした。相手がリクエストをキャンセルした可能性があります。',
            }))
            return
        else:
            async_to_sync(self.send)(text_data=json.dumps({
                'type': 'error',
                'error_type': 'room_error',
            }))
            return

    @database_sync_to_async
    def create_message(self, message_data, time, me):
        try:
            room = Room.objects.get(id=self.room_id)
            Message.objects.create(
                room=room,
                id=message_data['message_id'],
                content=message_data['message'],
                time=time,
                user=me,
            )
        except Exception as e:
            raise

    @database_sync_to_async
    def get_room_users(self, room):
        return {'request_user': room.request_user, 'response_user': room.response_user}

    @database_sync_to_async
    def turn_on_message_stored(self, is_request_user, message_id=None, room_id=None):
        try:
            if message_id: # for one message
                message = Message.objects.get(id=message_id)
                if is_request_user: # if I'm request user
                    message.is_stored_on_request = True
                else:  # if I'm response user
                    message.is_stored_on_response = True
                message.save()

            elif room_id: # for all messages in the room
                upd_messages = []
                if is_request_user: # if I'm request user
                    messages = Message.objects.filter(room__id=room_id, is_stored_on_request=False)
                    for message in messages:
                        message.is_stored_on_request = True
                        upd_messages.append(message)
                    Message.objects.bulk_update(upd_messages, fields=['is_stored_on_request'])
                else:  # if I'm response user
                    messages = Message.objects.filter(room__id=room_id, is_stored_on_response=False)
                    for message in messages:
                        message.is_stored_on_response = True
                        upd_messages.append(message)
                    Message.objects.bulk_update(upd_messages, fields=['is_stored_on_response'])
        except Exception as e:
            raise

    @database_sync_to_async
    def get_not_stored_messages_data(self, room, is_request_user, me):
        try:
            if is_request_user: # if I'm request user
                messages = Message.objects.filter(room=room, is_stored_on_request=False).order_by('time')
            else: # if I'm response user
                messages = Message.objects.filter(room=room, is_stored_on_response=False).order_by('time')
            return MessageSerializer(messages, many=True, context={'me': me}).data
        except Exception as e:
            raise