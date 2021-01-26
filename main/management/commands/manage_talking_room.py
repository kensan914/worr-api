from django.core.management.base import BaseCommand
from fullfii.chat.time_managers import manage_talking_time


class Command(BaseCommand):
    help = '1分ごとに実行. ' \
           'talking_roomを調べ、開始後2週間(20160分)経過していたらend処理を行う' \
           '開始後2週間経過5分前(20155分)達したらアラートを出す'

    def handle(self, *args, **options):
        pass
        # v2.0.0では見送り
        # manage_talking_time(end_minutes=20160, alert_minutes=20155)
