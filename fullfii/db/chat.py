import random
from chat.models import TalkTicket


def create_talk_ticket(owner, worry):
    talk_tickets = TalkTicket.objects.filter(
        owner=owner,
        worry=worry,
    )
    if talk_tickets.exists():
        talk_ticket = talk_tickets.first()
        talk_ticket.is_active = True
        talk_ticket.save()
    else:
        talk_ticket = TalkTicket(
            owner=owner,
            worry=worry,
            is_speaker=(random.randint(0, 1) == 0),
        )
        talk_ticket.save()
    return talk_ticket
