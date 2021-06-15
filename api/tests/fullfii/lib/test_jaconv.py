from django.test import TestCase

from fullfii.lib.jaconv import translate_into_kana, optimize_text


class TestJaconv(TestCase):
    def test_optimize_text(self):
        convertible_test = "ｋAげヤma"
        expected_output = "kaげやma"
        output = optimize_text(convertible_test)
        self.assertEquals(output, expected_output, msg="変換後textは正しいか")

        convertible_test = "影ﾔま"
        expected_output = "影やま"
        output = optimize_text(convertible_test)
        self.assertEquals(output, expected_output, msg="変換後textは正しいか(漢字含む)")

        convertible_test = "policeでス"
        expected_output = "policeです"
        output = optimize_text(convertible_test)
        self.assertEquals(output, expected_output, msg="変換後textは正しいか(英語含む)")

    def test_translate_into_kana(self):
        convertible_test = "ｋAげヤma"
        expected_output = {"is_success": True, "text": "かげやま"}
        output = translate_into_kana(convertible_test)
        self.assertEquals(
            output["is_success"], expected_output["is_success"], msg="変換成功したか"
        )
        self.assertEquals(output["text"], expected_output["text"], msg="変換後textは正しいか")

        unconvertible_test = "ｋAげヤmay"
        expected_output = {"is_success": False, "text": "かげやま"}
        output = translate_into_kana(unconvertible_test)
        self.assertEquals(
            output["is_success"], expected_output["is_success"], msg="変換成功したか"
        )
        self.assertEquals(output["text"], expected_output["text"], msg="変換後textは正しいか")
