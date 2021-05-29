from django.core.management.base import BaseCommand
import fullfii


class Command(BaseCommand):
    help = 'デフォルトルーム画像のinit'

    def handle(self, *args, **options):
        fullfii.init_default_room_image()
