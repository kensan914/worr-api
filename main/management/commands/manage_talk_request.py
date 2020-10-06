from django.core.management.base import BaseCommand
from fullfii.chat.time_managers import manage_talk_request_time


class Command(BaseCommand):
    help = '1分ごとに実行. ' \
           'not_started_roomを調べ、リクエスト開始後24時間(1440分)経過していたらcancel処理を行う'

    def handle(self, *args, **options):
        print('3')
        manage_talk_request_time(close_minutes=1440)
