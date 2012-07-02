"""
:mod:`date_trans`
~~~~~~~~~~~~~~~~~

Provides simple date transformations and date parsing for todo.next application.

.. created: 25.06.2012
.. moduleauthor:: Philipp Scholl <Phil@>
"""
from __future__ import print_function
import datetime, re
# if dateutil is installed, this makes everything a lot easier
USE_DATEUTIL = False
try:
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    USE_DATEUTIL = True
except ImportError:
    pass

re_partial_date = re.compile("(\d{1,2})\.(\d{1,2})\.", re.UNICODE)
re_rel_date = re.compile("^([+-]?)(\d{1,2}y)?(\d{1,2}m)?(\d{1,2}w)?(\d{1,3}d)?(\d{1,3}h)?$", re.IGNORECASE)


def get_relative_date(rel_string, reference_date = None):
    if not reference_date:
        reference_date = datetime.datetime.now()
    res = re_rel_date.findall(rel_string)[0]
    sign = res[0]
    dyears = int(res[1][:-1] or 0)
    dmonths = int(res[2][:-1] or 0)
    dweeks = int(res[3][:-1] or 0)
    ddays = int(res[4][:-1] or 0)
    dhours = int(res[5][:-1] or 0)
    rel = relativedelta(years=dyears, months=dmonths, days=ddays, weeks=dweeks, hours=dhours)
    if sign == "-":
        return reference_date - rel
    else:
        return reference_date + rel

def is_same_day(date1, date2):
    if not (isinstance(date1, datetime.datetime) and isinstance(date2, datetime.datetime)):
        return False
    return (date1.year, date1.month, date1.day) == (date2.year, date2.month, date2.day)

def shorten_date(date, today = None):
    if not isinstance(date, datetime.datetime):
        return date
    if not today:
        today = datetime.datetime.now()
    if is_same_day(today + datetime.timedelta(days=-1), date):
        # it is tomorrow
        if (date.hour, date.minute) == (0, 0):
            return "yesterday"
        else:
            return "yday," + date.strftime("%H:%M")
    if is_same_day(today, date):
        # it is today (in terms of reference date)
        if (date.hour, date.minute) == (0, 0):
            return "today"
        else:
            return date.strftime("%H:%M")
    if is_same_day(today + datetime.timedelta(days=1), date):
        # it is tomorrow
        if (date.hour, date.minute) == (0, 0):
            return "tomorrow"
        else:
            return "tomorrow," + date.strftime("%H:%M")
    else:
        if date.year == today.year:
            return date.strftime("%m-%d")
        else:
            return date.strftime("%Y-%m-%d")

weekdays = {
    "sunday":    0, "sun": 0, "so": 0,
    "monday":    1, "mon": 1, "mo": 1,
    "tuesday":   2, "tue": 2, "di": 2,
    "wednesday": 3, "wed": 3, "mi": 3,
    "thursday":  4, "thu": 4, "do": 4,
    "friday":    5, "fri": 5, "fr": 5,
    "saturday":  6, "sat": 6, "sa": 6,
    }

def get_date_by_weekday(weekday_name, reference_date = None):
    if not reference_date:
        reference_date = datetime.datetime.now()         
    wday_now = int(reference_date.strftime("%w"))
    wday_then = weekdays.get(weekday_name, None)
    if not wday_then:
        return None
    if wday_now == wday_then:
        # one week later
        return reference_date + datetime.timedelta(days = 7)
    elif wday_now > wday_then:
        # next week
        return reference_date + datetime.timedelta(days = (7 - wday_now))
    else:
        # still this week
        return reference_date + datetime.timedelta(days = (wday_then - wday_now))

def to_date(date_string, reference_date = None):
    """ parses a :class:`datetime` object from a given string
    
    :param date_string: a given string representing a (relative) date
    :type date_string: :class:`str`
    :param reference_date: a given date that serves as the reference point for relative date calculations. If ``None``, today's date 00:00am is used.
    :type reference_date: a :class:`datetime` object
    :return: :class:`datetime` object representing the desired date, or if not parsable, the given date string prepended with ``?``
    :rtype: :class:`datetime` or :class:`str`
    """
    if not date_string:
        return None
    now = datetime.datetime.now()
    if not reference_date:
        # reference date is today (without hours / min)
        reference_date = datetime.datetime(now.year, now.month, now.day)
    # normalize date string
    date_string = date_string.strip().lower()
    # first handle special cases:
    if date_string in ["today", "td", ""]:
        # today
        return reference_date
    elif date_string in ["tomorrow", "tm"]:
        # tomorrow
        return reference_date + datetime.timedelta(days=1)
    elif date_string in weekdays:
        # a weekday was given
        return get_date_by_weekday(date_string, reference_date)
    elif re_rel_date.match(date_string):
        if USE_DATEUTIL:
            # a relative timespan like "-1y5w2d" (1 year, 5 weeks and 2 days)
            return get_relative_date(date_string, reference_date)
    # clean underscores
    if "_" in date_string:
        date_string = date_string.replace("_", " ")
    try:
        if USE_DATEUTIL:
            # try to delegate parsing task to dateutil
            return parse(date_string, default=reference_date)
        else:
            # FIXME: fix format string
            return datetime.datetime.strptime(date_string, "%Y-%m-%d_H:%M")
    except:
        # date of form xx.xx.
        match = re_partial_date.match(date_string)
        if match:
            month, day = int(match.group(2)), int(match.group(1))
            if month > 12 and day < 12:
                month, day = day, month
            result = datetime.datetime(now.year, month, day)
            if now > result:
                # FIXME: check for leap year
                # timedelta has no year!
                result = datetime.datetime(now.year + 1, month, day)
            return result
        else:
            # show that we could not interpret the date string
            if not date_string.startswith("?"):
                result =  "?" + date_string.replace(" ", "_")
            else:
                result = date_string.replace(" ", "_")
            return result

def from_date(date):
    if not date:
        return ""
    elif isinstance(date, basestring):
        return date
    else:
        if date.hour == 0 and date.minute == 0:
            return date.strftime("%Y-%m-%d")
        else:
            return date.strftime("%Y-%m-%d_%H:%M")