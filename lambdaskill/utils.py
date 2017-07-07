import aniso8601
import datetime
import re


SEASON_DICT = {'WI': '12', 'SP': '03', 'SU': '06', 'FA': '09'}
SEASON_PATTERN = re.compile('^\d{4}-(WI|SP|SU|FA)$')
WEEKEND_PATTERN = re.compile('^\d{4}-W\d{2}-WE$')
TIME_DICT = {'AM': ((0, 0, 0), (11, 59, 59)),
             'PM': ((12, 0, 0), (23, 59, 59)),
             'MO': ((0, 0, 0), (11, 59, 59)),
             'AF': ((12, 0, 0), (16, 59, 59)),
             'EV': ((17, 0, 0), (19, 59, 59)),
             'NI': ((20, 0, 0), (23, 59, 59))}


def parse_date(amzdate):
    if SEASON_PATTERN.search(amzdate):
        start = aniso8601.parse_date('{}-{}-01'.format(amzdate[:4], SEASON_DICT[amzdate[-2:]]))
        yd = (start.month + 3) // 12
        md = (start.month + 3) % 12
        end = datetime.datetime(year=start.year + yd,
                                month=start.month + md,
                                day=1) - datetime.timedelta(days=1)
        return start, end
    elif WEEKEND_PATTERN.search(amzdate):
        return aniso8601.parse_date(amzdate[:-3] + "-6"), aniso8601.parse_date(amzdate[:-3] + "-7")
    elif amzdate.endswith('XX'):
        start = aniso8601.parse_date('{}{}'.format(amzdate[:2], '00'))
        end = datetime.datetime(year=start.year + 100,
                                month=1,
                                day=1) - datetime.timedelta(days=1)
        return start, end
    elif amzdate.endswith('X'):
        start = aniso8601.parse_date('{}{}'.format(amzdate[:3], '0'))
        end = datetime.datetime(year=start.year + 10,
                                month=1,
                                day=1) - datetime.timedelta(days=1)
        return start, end
    elif amzdate == 'PRESENT_REF':
        start = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + datetime.timedelta(days=1)
        return start, end
    return aniso8601.parse_date(amzdate)


def parse_time(amztime):
    if amztime in TIME_DICT:
        return tuple(datetime.time(*tt) for tt in TIME_DICT[amztime])
    return aniso8601.parse_time(amztime)


def parse_duration(amzduration):
    return aniso8601.parse_duration(amzduration)


def sequence_to_oxford_string(l):
    if len(l) > 2:
        return ', '.join([str(i) for i in l[:-1]]) + ", and " + str(l[-1])
    elif len(l) == 2:
        return ' and '.join([str(i) for i in l])
    elif len(l) > 0:
        return str(l[0])
