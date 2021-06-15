import uuid

from django.utils import timezone
from factory.django import DjangoModelFactory
import factory
from factory.fuzzy import FuzzyInteger, FuzzyText, FuzzyChoice

from account.models import Account, Gender, Job


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    id = factory.LazyFunction(uuid.uuid4)
    username = FuzzyText(length=15)
    gender = FuzzyChoice(Gender.choices)
    is_secret_gender = False
    job = FuzzyChoice(Job.choices)
    introduction = FuzzyText(length=250)
    device_token = ""
    is_active = True

    @factory.post_generation
    def hidden_rooms(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for _hidden_room in extracted:
                self.hidden_rooms.add(_hidden_room)

    @factory.post_generation
    def blocked_rooms(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for _blocked_room in extracted:
                self.blocked_rooms.add(_blocked_room)

    is_superuser = False
    loggedin_at = timezone.now()
    date_joined = timezone.now()
