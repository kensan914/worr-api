from django.core.management.base import BaseCommand
from account.models import Account, Gender


class Command(BaseCommand):
    help = '全アカウントのgenderを適合. secretのアカウントは'

    def handle(self, *args, **options):
        for account in Account.objects.all():
            if account.gender == 'secret':
                print('{}さんの性別がsecretです'.format(account.username))
                account.is_secret_gender = True
                account.gender = Gender.NOTSET
                account.save()
