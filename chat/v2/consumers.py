from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
import json
from channels.layers import get_channel_layer
from account.models import Status
from chat.serializers import MessageSerializer
from main.consumers import JWTAsyncWebsocketConsumer, NotificationConsumer
from main.models import NotificationType
from ..models import *
import fullfii


class ChatConsumerV2(JWTAsyncWebsocketConsumer):
    groups = ['broadcast']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = self.scope['url_route']['kwargs']['room_id'] if 'room_id' in self.scope['url_route']['kwargs'] else ''
        self.is_request_user = True

    @classmethod
    def get_group_name(cls, _id):
        return 'room_{}'.format(str(_id))

    async def receive_auth(self, received_data):
        self.group_name = self.get_group_name(self.room_id)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
        if me is None:
            # 401 Unauthorized
            await self.disconnect(4001)
            print('401 Unauthorized')
            return
        self.me_id = me.id

        result = await self.get_room()
        if result:
            room = result
        else:
            await self.close()
            return

        room_users = await self.get_room_users(room)
        if room_users['request_user'].id == self.me_id:  # if I'm request user
            self.is_request_user = True
            target_user = room_users['response_user']
        elif room_users['response_user'].id == self.me_id:  # if I'm response user
            self.is_request_user = False
            target_user = room_users['request_user']
            # If init is true, set response notification to request user
            if received_data['init']:
                await self.start_talk(room)  # start talk
                worried_user_id = await self.get_worried_user_id(room)
                await NotificationConsumer.send_notification_async(recipient=target_user, subject=me, notification_type=NotificationType.TALK_RESPONSE, context={
                    'room_id': str(self.room_id),
                    'worried_user_id': str(worried_user_id),
                })
        else:
            raise

        # change to talking
        _me = await self.change_status(me, Status.TALKING)
        me = _me if _me is not None else me
        user_data = await self.get_me_data(me)

        target_user.status = Status.TALKING
        target_user_data = await self.get_user_data(user=target_user)
        await self.send(text_data=json.dumps({
            'type': 'auth', 'room_id': str(self.room_id), 'target_user': target_user_data, 'profile': user_data
        }))

        # Send messages that you haven't stored yet
        not_stored_messages_data = await self.get_not_stored_messages_data(room, self.is_request_user, me)
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

            me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)

            await self.create_message(received_data, time, me)
            await self.channel_layer.group_send(self.group_name, {
                    'type': 'chat_message',
                    'message_id': message_id,
                    'message': message,
                    'time': time.strftime('%Y/%m/%d %H:%M:%S'),
                    'sender_channel_name': self.channel_name,
            })

        elif received_type == 'store':
            message_id = received_data['message_id']
            me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
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

    async def end_talk(self, event):
        try:
            _type = None
            if event['alert']:
                _type = 'end_talk_alert'
            elif event['time_out']:
                _type = 'end_talk_time_out'
            else:
                if str(self.me_id) != event['sender_id']:
                    _type = 'end_talk'
            if _type is not None:
                me = await self.get_user(self.me_id)
                user_data = await self.get_me_data(me)
                await self.send(text_data=json.dumps({
                    'type': _type,
                    'profile': user_data,
                }))
        except Exception as e:
            raise

    @database_sync_to_async
    def get_room(self, is_allow_send=True):
        rooms = Room.objects.filter(id=self.room_id)
        if rooms.count() == 1:
            return rooms.first()
        elif rooms.count() == 0:
            if is_allow_send:
                async_to_sync(self.send)(text_data=json.dumps({
                    'type': 'error',
                    'error_type': 'not_found_room',
                    'message': 'お探しのトークルームは見つかりませんでした。相手がリクエストをキャンセルした可能性があります。',
                }))
            return
        else:
            if is_allow_send:
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
    def get_worried_user_id(self, room):
        if room.is_worried_request_user:
            return room.request_user.id
        else:
            return room.response_user.id

    @database_sync_to_async
    def turn_on_message_stored(self, is_request_user, message_id=None, room_id=None):
        try:
            if message_id:  # for one message
                message = Message.objects.get(id=message_id)
                if is_request_user:  # if I'm request user
                    message.is_stored_on_request = True
                else:  # if I'm response user
                    message.is_stored_on_response = True
                message.save()

            elif room_id:  # for all messages in the room
                upd_messages = []
                if is_request_user:  # if I'm request user
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
            if is_request_user:  # if I'm request user
                messages = Message.objects.filter(room=room, is_stored_on_request=False).order_by('time')
            else:  # if I'm response user
                messages = Message.objects.filter(room=room, is_stored_on_response=False).order_by('time')
            return MessageSerializer(messages, many=True, context={'me': me}).data
        except Exception as e:
            raise

    @database_sync_to_async
    def start_talk(self, room):
        if not room.is_start:
            room.is_start = True
            room.started_at = timezone.now()
            room.save()

    @classmethod
    def send_end_talk(cls, room_id, time_out=False, alert=False, sender_id=None):
        group_name = cls.get_group_name(room_id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'end_talk',
            'time_out': time_out,
            'alert': alert,
            'sender_id': str(sender_id) if sender_id else None,
        })
