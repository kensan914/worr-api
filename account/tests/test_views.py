# from rest_framework.test import APITestCase
#
# from account.v4.serializers import MeSerializer
# from account.tests import factories
#
#
# class TestMemberListView(APITestCase):
#     URL = "/api/members/"
#
#     def setUp(self):
#         group_sakura = factories.GroupFactory(group_id=1, key="sakura")
#         group_hinata = factories.GroupFactory(group_id=2, key="hinata")
#         group_keyaki = factories.GroupFactory(group_id=3, key="keyaki", is_active=False)
#
#         # 櫻坂1期生(a)
#         self.member_sakura_g1_a = factories.MemberFactory(
#             belonging_group=group_sakura, generation=1, full_kana="a"
#         )
#         # 櫻坂1期生(b)
#         self.member_sakura_g1_b = factories.MemberFactory(
#             belonging_group=group_sakura, generation=1, full_kana="b"
#         )
#         # 櫻坂1期生(c). 卒業生
#         self.member_sakura_g1_c = factories.MemberFactory(
#             belonging_group=group_sakura, generation=1, graduate=True, full_kana="c"
#         )
#         # 櫻坂2期生(a). 仮メンバー(新2期生)
#         self.member_sakura_g2_a = factories.MemberFactory(
#             belonging_group=group_sakura,
#             generation=2,
#             independence=False,
#             temporary=True,
#             full_kana="a",
#         )
#         # 日向坂2期生(a)
#         self.member_hinata_g2_a = factories.MemberFactory(
#             belonging_group=group_hinata, generation=2, full_kana="a"
#         )
#         # 日向坂0期生(a). その他メンバー
#         self.member_hinata_g0_a = factories.MemberFactory(
#             belonging_group=group_hinata, generation=0, is_other=True, full_kana="a"
#         )
#         # 欅坂1期生(a)
#         self.member_keyaki_g1_a = factories.MemberFactory(
#             belonging_group=group_keyaki, generation=1, full_kana="a"
#         )
#
#     def tearDown(self):
#         pass
#
#     def test_GET_200(self):
#         """/members/へのGETリクエスト (200)"""
#         response = self.client.get(self.URL, format="json")
#         self.assertEqual(response.status_code, 200, msg="HTTPステータス200が返る")
#
#         expected_json = {
#             "sakura": {
#                 "1": MemberSerializer(
#                     [
#                         self.member_sakura_g1_a,
#                         self.member_sakura_g1_b,
#                         self.member_sakura_g1_c,
#                     ],
#                     many=True,
#                 ).data,
#                 "2": MemberSerializer(
#                     [
#                         self.member_sakura_g2_a,
#                     ],
#                     many=True,
#                 ).data,
#             },
#             "hinata": {
#                 "2": MemberSerializer(
#                     [
#                         self.member_hinata_g2_a,
#                     ],
#                     many=True,
#                 ).data,
#                 "0": MemberSerializer(
#                     [
#                         self.member_hinata_g0_a,
#                     ],
#                     many=True,
#                 ).data,
#             },
#         }
#         self.assertJSONEqual(response.content, expected_json, msg="正常なメンバーリストJSONが返る")
