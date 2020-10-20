def generate_birthday(birthday):
    year = birthday.year
    month = birthday.month
    day = birthday.day
    return { 'text': '{}年{}月{}日'.format(year, month, day), 'year': year, 'month': month, 'day': day, }