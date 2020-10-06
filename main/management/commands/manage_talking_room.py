from django.core.management.base import BaseCommand
from fullfii.chat.time_managers import manage_talking_time


class Command(BaseCommand):
    help = '1分ごとに実行. ' \
           'talking_roomを調べ、開始後24時間(1440分)経過していたらend処理を行う' \
           '開始後23時間55分(1435分)経過していたらアラートを出す'

    def handle(self, *args, **options):
        print('4')
        manage_talking_time(end_minutes=1440, alert_minutes=1435)
