from django.core.management.base import BaseCommand
import fullfii


class Command(BaseCommand):
    help = 'Initialize database.' \
           'memberList.txtに変更を加え、コマンドを実行すれば、変更箇所だけDBに反映されます。'

    def handle(self, *args, **options):
        fullfii.InitFeature().init()
        fullfii.InitGenreOfWorries().init()
        fullfii.InitScaleOfWorries().init()
