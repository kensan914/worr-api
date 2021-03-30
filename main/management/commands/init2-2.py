from django.core.management.base import BaseCommand
import fullfii
from account.models import Account, GenreOfWorries
from asgiref.sync import async_to_sync
from chat.models import TalkTicket, TalkStatus
from fullfii import create_talking_room, start_talk
from django.utils import timezone


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        # to_user = Account.objects.get(
        #     id='e6ff91e0-bc6d-4a21-b01b-501b4cf6076d')
        # user = Account.objects.get(id='d281fceb-8d4b-4fab-89ae-17320e046f62')
        # genreOfWorry = GenreOfWorries.objects.get(key='g')

        # # send fcm(SEND_MESSAGE)
        # async_to_sync(fullfii.send_fcm)(to_user, {
        #     'type': 'SEND_MESSAGE',
        #     'user': user,
        #     'message': 'test',
        # })

        # # send fcm(MATCH_TALK)
        # async_to_sync(fullfii.send_fcm)(to_user, {
        #     'type': 'MATCH_TALK',
        #     'genreOfWorry': genreOfWorry,
        # })

        # # send fcm(THUNKS)
        # async_to_sync(fullfii.send_fcm)(to_user, {
        #     'type': 'THUNKS',
        #     'user': user,
        # })

        # loggedin_minutes_class = [2*24*60, 7*24*60, -1]
        # loggedin_minutes_class = [1*24*60, 2*24*60, -1]
        # talk_tickets_split_by_class = []
        # for i in range(len(loggedin_minutes_class)):
        #     talk_tickets_split_by_class.append([])

        # for talk_ticket in TalkTicket.objects.all():
        #     elapsed_seconds = (
        #         timezone.now() - talk_ticket.owner.loggedin_at).total_seconds()
        #     elapsed_minutes = elapsed_seconds / 60

        #     print(elapsed_minutes)

        #     for i, loggedin_minutes in enumerate(loggedin_minutes_class):
        #         if elapsed_minutes < loggedin_minutes:
        #             talk_tickets_split_by_class[i].append(talk_ticket.pk)
        #             break
        #         elif loggedin_minutes == -1:
        #             talk_tickets_split_by_class[i].append(talk_ticket.pk)
        #             break

        # for talk_ticket_ids in talk_tickets_split_by_class:
        #     talk_tickets = TalkTicket.objects.filter(pk__in=talk_ticket_ids)
        #     print(
        #         'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        #     print(talk_tickets)

        # fullfii.start_matching(version=3)

        # トーク済みアカウントリセット
        for account in Account.objects.all():
            account.talked_accounts.clear()

        # talking => waiting
        # for talk_ticket in TalkTicket.objects.all():
        #     if talk_ticket.status == TalkStatus.TALKING:
        #         talk_ticket.status = TalkStatus.WAITING
        #         talk_ticket.save()
