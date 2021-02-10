from django.core.management.base import BaseCommand
import fullfii
from chat.models import TalkingRoom, TalkStatus


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        for i, talking_room in enumerate(TalkingRoom.objects.filter(is_end=True)):
            print('{}'.format(talking_room.speaker_ticket.owner))
            if talking_room.speaker_ticket.status == TalkStatus.TALKING:
                fullfii.end_talk_ticket(talking_room.speaker_ticket)
                print('{}を終了させました'.format(talking_room.speaker_ticket.owner))
            if talking_room.listener_ticket.status == TalkStatus.TALKING:
                fullfii.end_talk_ticket(talking_room.listener_ticket)
                print('{}を終了させました'.format(talking_room.speaker_ticket.owner))
