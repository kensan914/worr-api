from datetime import datetime
import pandas as pd
import pytz
from django.utils import timezone


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
    timezoneを含むdatetimeのstring(ex: '2018-06-18 15:03:55 Etc/GMT')をsettings.TIME_ZONEで設定されているタイムゾーンに
    ローカライズしたdatetime(naive)に変換
    :param tz_str:
    :param dt_format:
    :return: datetime
    """
    dt, tz = tz_str.rsplit(maxsplit=1)
    _datetime = datetime.strptime(dt, dt_format).replace(tzinfo=pytz.timezone(tz))
    _local_datetime = _datetime.astimezone(timezone.get_current_timezone())
    return _local_datetime.replace(tzinfo=None)
