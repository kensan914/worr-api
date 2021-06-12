import uuid

from django.utils import timezone
from factory.django import DjangoModelFactory
import factory
from factory.fuzzy import FuzzyInteger, FuzzyText, FuzzyChoice

from account.tests.factories import AccountFactory
from chat.models import RoomV4, DefaultRoomImage


class DefaultRoomImageFactory(DjangoModelFactory):
    class Meta:
        model = DefaultRoomImage

    id = uuid.uuid4()
    file_name = FuzzyText(length=100)
    image = factory.django.ImageField()


class RoomV4Factory(DjangoModelFactory):
    class Meta:
        model = RoomV4

    id = uuid.uuid4()
    name = FuzzyText(length=60)
    image = factory.django.ImageField()
    default_image = factory.SubFactory(DefaultRoomImageFactory)
    owner = factory.SubFactory(AccountFactory)

    @factory.post_generation
    def participants(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for _participant in extracted:
                self.participants.add(_participant)

    @factory.post_generation
    def left_members(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for _left_member in extracted:
                self.left_members.add(_left_member)

    @factory.post_generation
    def closed_members(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for _closed_member in extracted:
                self.closed_members.add(_closed_member)

    max_num_participants = 1
    is_exclude_different_gender = False
    created_at = timezone.now()
    is_end = False
    is_active = False
