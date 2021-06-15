import csv


def fetch_csv_as_dict(csv_path):
    """CSV => dict"""
    fin = open(csv_path, "rt", encoding="utf-8")
    csv_dict_read_result = csv.DictReader(
        fin,
        delimiter=",",
        doublequote=True,
        lineterminator="\r\n",
        quotechar='"',
        skipinitialspace=True,
    )

    csv_dict = {}
    for column in csv_dict_read_result:
        for key, val in column.items():
            if key in csv_dict:
                # blank or 未設定はappendしない
                if val:
                    csv_dict[key].append(val)
            else:
                # 初期化
                csv_dict[key] = [val]

    return csv_dict
