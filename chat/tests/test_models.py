from django.test import TestCase
from chat.models import RoomV4
from chat.tests import factories


class TestRoomV4Model(TestCase):
    def setUp(self):
        self.account_test_data = factories.RoomV4Factory()

    def test_create(self):
        """RoomV4のcreateをテスト"""
        self.assertEquals(RoomV4.objects.all().count(), 1, msg="作成されている")

        created_account = RoomV4.objects.all().first()
        self.assertEquals(created_account.id, self.account_test_data.id, msg="idが正常である")
        self.assertEquals(
            created_account.name, self.account_test_data.name, msg="nameが正常である"
        )
        self.assertEquals(
            created_account.image, self.account_test_data.image, msg="imageが正常である"
        )
        self.assertEquals(
            created_account.default_image.id,
            self.account_test_data.default_image.id,
            msg="default_imageが正常である",
        )
        self.assertEquals(
            created_account.owner.id,
            self.account_test_data.owner.id,
            msg="ownerが正常である",
        )
        self.assertEquals(
            created_account.participants,
            self.account_test_data.participants,
            msg="participantsが正常である",
        )
        self.assertEquals(
            created_account.left_members,
            self.account_test_data.left_members,
            msg="left_membersが正常である",
        )
        self.assertEquals(
            created_account.closed_members,
            self.account_test_data.closed_members,
            msg="closed_membersが正常である",
        )
        self.assertEquals(
            created_account.max_num_participants,
            self.account_test_data.max_num_participants,
            msg="max_num_participantsが正常である",
        )
        self.assertEquals(
            created_account.is_exclude_different_gender,
            self.account_test_data.is_exclude_different_gender,
            msg="is_exclude_different_genderが正常である",
        )
        self.assertEquals(
            created_account.created_at,
            self.account_test_data.created_at,
            msg="created_atが正常である",
        )
        self.assertEquals(
            created_account.is_end,
            self.account_test_data.is_end,
            msg="is_endが正常である",
        )
        self.assertEquals(
            created_account.is_active,
            self.account_test_data.is_active,
            msg="is_activeが正常である",
        )
