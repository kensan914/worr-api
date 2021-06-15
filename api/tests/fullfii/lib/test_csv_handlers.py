from django.test import TestCase

from fullfii.lib.csv_handlers import fetch_csv_as_dict


class TestCsvHandlers(TestCase):
    def test_fetch_csv_as_list(self):
        output = fetch_csv_as_dict("fullfii/lib/csv_handlers/test_data.csv")
        expected_output = {
            "r1": ["1_1", "2_1", "3_1", "4_1", "5_1"],
            "r2": ["1_2", "2_2", "3_2"],
        }
        self.assertDictEqual(output, expected_output, msg="fetch_csv_as_listの出力結果テスト")
