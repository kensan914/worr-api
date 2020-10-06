from django.core.management.base import BaseCommand
from fullfii.chat.time_managers import manage_after_talk_time


class Command(BaseCommand):
    help = '1分ごとに実行. ' \
           'end_roomを調べ、end後24時間(1440分)経過していたらend処理を行う'

    def handle(self, *args, **options):
        manage_after_talk_time(close_minutes=1440)
