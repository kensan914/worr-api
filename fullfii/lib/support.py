from datetime import datetime
import pandas as pd
import pytz


def calc_age(birthday):
    """
    誕生日を入力し、現在の年齢を出力
    :param birthday:
    :return: age
    """
    today = int(pd.to_datetime('today').strftime('%Y%m%d'))
    birthday = int(birthday.strftime('%Y%m%d'))
    return int((today - birthday) / 10000)


def cvt_tz_str_to_datetime(tz_str, dt_format='%Y-%m-%d %H:%M:%S'):
    """
    timezoneを含むdatetimeのstring(ex: '2018-06-18 15:03:55 Etc/GMT')をdatetimeに変換
    :param tz_str:
    :param dt_format:
    :return: datetime
    """
    dt, tz = tz_str.rsplit(maxsplit=1)
    return datetime.strptime(dt, dt_format).replace(tzinfo=pytz.timezone(tz))
