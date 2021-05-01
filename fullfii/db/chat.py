from account.models import GenreOfWorries
import random
from chat.models import TalkStatus, TalkTicket


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


def activate_talk_ticket(talk_ticket):
    """
    talkTicketを活性化状態に戻す, その時にstatusはstoppingに
    """
    talk_ticket.is_active = True
    talk_ticket.status = TalkStatus.STOPPING
    talk_ticket.save()
    return talk_ticket


def gene_length_participants():
    length_participants = {}
    for genreOfWorry in GenreOfWorries.objects.all():
        length_participants_by_worry = 0

        participant_talkTicket = TalkTicket.objects.filter(
            is_active=True,
            owner__is_active=True
        ).exclude(status=TalkStatus.STOPPING)
        try:
            # 悩みの絞り込み
            if genreOfWorry.value == 'just_want_to_talk':
                participant_talkTicket = participant_talkTicket.filter(
                    worry=genreOfWorry)
            else:
                just_want_to_talk = GenreOfWorries.objects.get(
                    value='just_want_to_talk')
                participant_talkTicket = participant_talkTicket.exclude(
                    worry=just_want_to_talk)
        except:
            participant_talkTicket = participant_talkTicket.filter(
                worry=genreOfWorry)

        length_participants_by_worry += participant_talkTicket.count()
        length_participants[genreOfWorry.key] = length_participants_by_worry

    return length_participants
