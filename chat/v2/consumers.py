import traceback
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
import json
from channels.layers import get_channel_layer
from account.v2.serializers import MeV2Serializer
from chat.v2.serializers import MessageV2Serializer
from main.consumers import JWTAsyncWebsocketConsumer
from ..models import *
import fullfii


class ChatConsumerV2(JWTAsyncWebsocketConsumer):
    groups = ['broadcast']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = self.scope['url_route']['kwargs']['room_id'] if 'room_id' in self.scope['url_route']['kwargs'] else ''
        self.is_speaker = True

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

        auth_response_data = {
            'type': 'auth',
            'room_id': str(self.room_id),
            'not_stored_messages': [],
            'is_already_ended': False,
        }

        room = await self.get_room()
        if room:
            room_users = await self.get_room_users(room)
            if room_users['speaker'].id == self.me_id:  # if I'm speaker
                self.is_speaker = True
            elif room_users['listener'].id == self.me_id:  # if I'm listener
                self.is_speaker = False

            # Messages that you haven't stored yet include in auth send.
            not_stored_messages_data = await self.get_not_stored_messages_data(room, self.is_speaker, me)
            if not_stored_messages_data:
                auth_response_data['not_stored_messages'] = not_stored_messages_data

            # If the talk has already ended, notice. (通常、アプリがquit間にトークの開始・終了が行われた時)
            is_already_ended = room.is_end
            if is_already_ended:
                auth_response_data['is_already_ended'] = is_already_ended

            # v2.3.6以前のユーザ用(v2.3.7移行はnot_stored_messages_dataをauth sendに含めてしまっているため)
            if not_stored_messages_data:
                await self.send(text_data=json.dumps({
                    'type': 'multi_chat_messages',
                    'room_id': str(self.room_id),
                    'messages': not_stored_messages_data,
                }))
        elif room == 0:
            # マッチング直後にchat wsコネクションを試みたとき(マッチング時にアプリを開いていた時)
            # roomをcreateした直後にself.get_room()した場合、roomがdoesNotExist判定になる(↓参考)
            # https://github.com/django/channels/issues/1110
            self.is_speaker = received_data['is_speaker'] if 'is_speaker' in received_data else True
        else:
            await self.close()
            print('room error.')
            return

        await self.send(text_data=json.dumps(auth_response_data))

    async def _receive(self, received_data):
        received_type = received_data['type']

        if received_type == 'chat_message':
            if 'message_id' in received_data and 'message' in received_data and 'token' in received_data:
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

                # send fcm(SEND_MESSAGE)
                room = await self.get_room()
                if room:
                    room_users = await self.get_room_users(room)
                    receiver = room_users['listener'] if room_users['speaker'].id == me.id else room_users['speaker']
                    receiver_talk_ticket = room.listener_ticket if room_users[
                        'speaker'].id == me.id else room.speaker_ticket

                    # sync_to_async(fullfii.send_fcm)(receiver, {
                    await fullfii.send_fcm(receiver, {
                        'type': 'SEND_MESSAGE',
                        'user': me,
                        'message': message,
                        'receiver_talk_ticket': receiver_talk_ticket
                    })
            else:
                # chat_message送信失敗
                pass

        elif received_type == 'store':
            if 'message_id' in received_data and 'token' in received_data:
                message_id = received_data['message_id']
                # me = await fullfii.authenticate_jwt(received_data['token'], is_async=True)
                await self.turn_on_message_stored(self.is_speaker, message_id=message_id)
            else:
                # store失敗
                pass

        elif received_type == 'store_by_room':
            await self.turn_on_message_stored(self.is_speaker, room_id=self.room_id)

        # フロントで既読処理が走った際に送信される
        elif received_type == 'read':
            if 'token' in received_data:
                await self.turn_on_read_all_messages(self.is_speaker, room_id=self.room_id)
            else:
                # read 失敗
                pass

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
    def get_room(self):
        rooms = TalkingRoom.objects.filter(id=self.room_id)
        if rooms.count() == 1:
            return rooms.first()
        elif rooms.count() == 0:
            return 0
        else:
            return

    @database_sync_to_async
    def create_message(self, message_data, time, me):
        try:
            room = TalkingRoom.objects.get(id=self.room_id)
            MessageV2.objects.create(
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
        return {'speaker': room.speaker_ticket.owner, 'listener': room.listener_ticket.owner}

    @database_sync_to_async
    def turn_on_read_all_messages(self, is_speaker, room_id):
        try:
            upd_messages = []
            if is_speaker:  # if I'm speaker
                messages = MessageV2.objects.filter(
                    room__id=room_id, is_read_speaker=False)
                for message in messages:
                    message.is_read_speaker = True
                    upd_messages.append(message)
                MessageV2.objects.bulk_update(
                    upd_messages, fields=['is_read_speaker'])
            else:  # if I'm listener
                messages = MessageV2.objects.filter(
                    room__id=room_id, is_read_listener=False)
                for message in messages:
                    message.is_read_listener = True
                    upd_messages.append(message)
                MessageV2.objects.bulk_update(
                    upd_messages, fields=['is_read_listener'])
        except:
            traceback.print_exc()

    @database_sync_to_async
    def turn_on_message_stored(self, is_speaker, message_id=None, room_id=None):
        try:
            if message_id:  # for one message
                message = MessageV2.objects.get(id=message_id)
                if is_speaker:  # if I'm speaker
                    message.is_stored_on_speaker = True
                else:  # if I'm listener
                    message.is_stored_on_listener = True
                message.save()

            elif room_id:  # for all messages in the room
                upd_messages = []
                if is_speaker:  # if I'm speaker
                    messages = MessageV2.objects.filter(
                        room__id=room_id, is_stored_on_speaker=False)
                    for message in messages:
                        message.is_stored_on_speaker = True
                        upd_messages.append(message)
                    MessageV2.objects.bulk_update(
                        upd_messages, fields=['is_stored_on_speaker'])
                else:  # if I'm listener
                    messages = MessageV2.objects.filter(
                        room__id=room_id, is_stored_on_listener=False)
                    for message in messages:
                        message.is_stored_on_listener = True
                        upd_messages.append(message)
                    MessageV2.objects.bulk_update(
                        upd_messages, fields=['is_stored_on_listener'])
        except Exception as e:
            raise

    @database_sync_to_async
    def get_not_stored_messages_data(self, room, is_speaker, me):
        try:
            if is_speaker:  # if I'm speaker
                messages = MessageV2.objects.filter(
                    room=room, is_stored_on_speaker=False).order_by('time')
            else:  # if I'm listener
                messages = MessageV2.objects.filter(
                    room=room, is_stored_on_listener=False).order_by('time')
            return MessageV2Serializer(messages, many=True, context={'me': me}).data
        except Exception as e:
            raise

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

    @database_sync_to_async
    def get_me_data(self, user):
        return MeV2Serializer(user).data
