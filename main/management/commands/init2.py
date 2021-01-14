from django.core.management.base import BaseCommand
import fullfii
from chat.models import TalkTicket


class Command(BaseCommand):
    help = 'マッチングシステムスタート'

    def handle(self, *args, **options):
        for i, user in enumerate(fullfii.get_all_accounts()):
            for j, worry in enumerate(user.genre_of_worries.all()):
                talk_tickets = TalkTicket.objects.filter(owner=user, worry=worry)
                if talk_tickets.exists():
                    talk_ticket = talk_tickets.first()
                else:
                    talk_ticket = TalkTicket(
                        owner=user,
                        worry=worry,
                        is_speaker=bool(i%2),
                    )
                    talk_ticket.save()


        # start マッチング
        fullfii.start_matching()
