from django.core.management.base import BaseCommand
from fullfii.chat.time_managers import manage_talk_request_time


class Command(BaseCommand):
    help = '1分ごとに実行. ' \
           'not_started_roomを調べ、リクエスト開始後3日(4320分)経過していたらcancel処理を行う'

    def handle(self, *args, **options):
        manage_talk_request_time(close_minutes=4320)
