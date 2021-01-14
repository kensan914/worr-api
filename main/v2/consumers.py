from channels.db import database_sync_to_async
import json
from account.v2.serializers import MeV2Serializer
from main.consumers import NotificationConsumer


class NotificationV2Consumer(NotificationConsumer):
    async def get_group_name(self, _id):
        return 'notification_v2_{}'.format(str(_id))

    @database_sync_to_async
    def get_me_data(self, user):
        return MeV2Serializer(user).data

    async def notice_talk(self, event):
        try:
            appended_data = event['context']
            data = {'type': 'notice_talk'}
            data.update(appended_data)
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            raise
