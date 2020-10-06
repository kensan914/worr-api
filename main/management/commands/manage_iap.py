from django.core.management.base import BaseCommand
from fullfii.lib.iap import manage_iap_expires_date


class Command(BaseCommand):
    help = '5分ごとに実行.' \
           'Iapを調べ、有効期限日時まで12時間(720分)以内であれば、レシート検証をする' \
           'debug時、2分いない'

    def handle(self, *args, **options):
        manage_iap_expires_date(within_minutes=2)
