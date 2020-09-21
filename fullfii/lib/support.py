import pandas as pd

def calc_age(birthday):
    """
    誕生日を入力し、現在の年齢を出力
    :param birthday:
    :return: age
    """
    today = int(pd.to_datetime('today').strftime('%Y%m%d'))
    birthday = int(birthday.strftime('%Y%m%d'))
    return int((today - birthday) / 10000)