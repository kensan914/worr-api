from django.core.management.base import BaseCommand
import fullfii
from account.models import Account, GenreOfWorries
from asgiref.sync import async_to_sync


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        to_user = Account.objects.get(
            id='e6ff91e0-bc6d-4a21-b01b-501b4cf6076d')
        user = Account.objects.get(id='d281fceb-8d4b-4fab-89ae-17320e046f62')
        genreOfWorry = GenreOfWorries.objects.get(key='g')

        # send fcm(SEND_MESSAGE)
        async_to_sync(fullfii.send_fcm)(to_user, {
            'type': 'SEND_MESSAGE',
            'user': user,
            'message': 'test',
        })

        # send fcm(MATCH_TALK)
        async_to_sync(fullfii.send_fcm)(to_user, {
            'type': 'MATCH_TALK',
            'genreOfWorry': genreOfWorry,
        })

        # send fcm(THUNKS)
        async_to_sync(fullfii.send_fcm)(to_user, {
            'type': 'THUNKS',
            'user': user,
        })
