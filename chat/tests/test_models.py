from django.test import TestCase
from chat.models import RoomV4
from chat.tests import factories


class TestRoomV4Model(TestCase):
    def setUp(self):
        self.room_test_data = factories.RoomV4Factory()

    def test_create(self):
        """RoomV4のcreateをテスト"""
        self.assertEquals(RoomV4.objects.all().count(), 1, msg="作成されている")

        created_room = RoomV4.objects.first()
        self.assertEquals(created_room.id, self.room_test_data.id, msg="idが正常である")
        self.assertEquals(created_room.name, self.room_test_data.name, msg="nameが正常である")
        self.assertEquals(
            created_room.image, self.room_test_data.image, msg="imageが正常である"
        )
        self.assertEquals(
            created_room.default_image.id,
            self.room_test_data.default_image.id,
            msg="default_imageが正常である",
        )
        self.assertEquals(
            created_room.owner.id,
            self.room_test_data.owner.id,
            msg="ownerが正常である",
        )
        self.assertEquals(
            created_room.participants,
            self.room_test_data.participants,
            msg="participantsが正常である",
        )
        self.assertEquals(
            created_room.left_members,
            self.room_test_data.left_members,
            msg="left_membersが正常である",
        )
        self.assertEquals(
            created_room.closed_members,
            self.room_test_data.closed_members,
            msg="closed_membersが正常である",
        )
        self.assertEquals(
            created_room.max_num_participants,
            self.room_test_data.max_num_participants,
            msg="max_num_participantsが正常である",
        )
        self.assertEquals(
            created_room.is_exclude_different_gender,
            self.room_test_data.is_exclude_different_gender,
            msg="is_exclude_different_genderが正常である",
        )
        self.assertEquals(
            created_room.created_at,
            self.room_test_data.created_at,
            msg="created_atが正常である",
        )
        self.assertEquals(
            created_room.is_end,
            self.room_test_data.is_end,
            msg="is_endが正常である",
        )
        self.assertEquals(
            created_room.is_active,
            self.room_test_data.is_active,
            msg="is_activeが正常である",
        )

    def test_update(self):
        """RoomV4のupdateをテスト"""
        created_room = RoomV4.objects.first()
        _name = "変更後ルーム名"
        _is_end = True
        _is_active = False
        created_room.name = _name
        created_room.is_end = _is_end
        created_room.is_active = _is_active
        created_room.save()

        update_room = RoomV4.objects.first()
        self.assertEquals(update_room.name, _name, msg="nameが正常である")
        self.assertEquals(
            update_room.is_end,
            _is_end,
            msg="is_endが正常である",
        )
        self.assertEquals(
            update_room.is_active,
            _is_active,
            msg="is_activeが正常である",
        )
