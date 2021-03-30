from django.core.management.base import BaseCommand
from fullfii.chat.time_managers import manage_talking_time


class Command(BaseCommand):
    help = '1分ごとに実行. ' \
           'talking_roomを調べ、最終メッセージ後48時間経過していたらend処理を行う' \
           '最終メッセージ後48時間経過10分前達したらアラートを出す'

    def handle(self, *args, **options):
        # manage_talking_time(end_minutes=2*24*60, alert_minutes=2*24*60-10)
        manage_talking_time(end_minutes=0.4, alert_minutes=0.1)  # TODO:
