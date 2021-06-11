import random
from django.core.management.base import BaseCommand
from account.models import Account, Feature, GenreOfWorries, ScaleOfWorries


class Command(BaseCommand):
    help = "N人の仮ユーザを作成"

    def handle(self, *args, **options):
        user_N = 100
        probability_num = 2  # 1 / probability_num

        for i in range(user_N):
            user = Account(
                username="仮ユーザ({})".format(i),
                email="kari{}@gmail.com".format(i),
                password="kariuser{}".format(i),
            )
            user.save()
            user.features.set(
                Feature.objects.filter(
                    key__in=self.get_random_params_keys(
                        Feature.objects.all(), probability_num
                    )
                )
            )
            user.genre_of_worries.set(
                GenreOfWorries.objects.filter(
                    key__in=self.get_random_params_keys(
                        GenreOfWorries.objects.all(), probability_num
                    )
                )
            )
            user.scale_of_worries.set(
                ScaleOfWorries.objects.filter(
                    key__in=self.get_random_params_keys(
                        ScaleOfWorries.objects.all(), probability_num
                    )
                )
            )
            print("仮ユーザ({})を作成しました".format(i))

    def get_random_params_keys(self, params_records, probability_num):
        keys = []
        for params_record in params_records:
            r = random.randint(1, probability_num)
            if r == 1:
                keys.append(params_record.key)
        return keys
