from django.core.management.base import BaseCommand
from fullfii.lib.iap import manage_iap_expires_date


class Command(BaseCommand):
    help = '5分ごとに実行.' \
           'Iapを調べ、有効期限日時まで12時間(720分)以内であれば、レシート検証をする.' \
           'debug時、1分ごとに実行. 2分以内でレシート検証.' \
           '自動更新失敗中のIapは有効期限が過ぎた瞬間に期限切れに変更'

    def handle(self, *args, **options):
        manage_iap_expires_date(within_minutes=720)
