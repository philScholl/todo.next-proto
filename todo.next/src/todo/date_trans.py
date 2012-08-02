"""
:mod:`date_trans`
~~~~~~~~~~~~~~~~~

Provides simple date transformations and date parsing for todo.next application.

.. created: 25.06.2012
.. moduleauthor:: Philipp Scholl <Phil@>
"""
from __future__ import print_function

from config import ConfigBorg

import datetime, re, calendar

# if dateutil is installed, this makes everything a lot easier
USE_DATEUTIL = False
try:
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    USE_DATEUTIL = True
except ImportError:
    pass

# partial date without year (German form, e.g. '21.12.')
re_partial_date = re.compile("(\d{1,2})\.(\d{1,2})\.", re.UNICODE)
# relative form of date, e.g. 'm1w2d' (minus 1 week, 2 days). Month support needs :mod:`dateutil
re_rel_date = re.compile("^([+-pm]?)(\d{1,2}y)?(\d{1,2}m)?(\d{1,2}w)?(\d{1,3}d)?(\d{1,3}h)?$", re.IGNORECASE)

conf = ConfigBorg()

def add_years(date, nr_of_years):
    """adds years to the given date
    
    This is only a problem with the 29th of February. This is handled here.
    
    :param date: the date
    :type date: :class:`datetime.datetime`
    :param nr_of_years: the number of years to add to the date
    :type nr_of_years: int
    :return: the date with the added years
    :rtype: :class:`datetime.datetime`
    """
    if date.month == 2 and date.day == 29:
        if not calendar.isleap(date.year + nr_of_years):
            return date.replace(year=date.year+nr_of_years, day=28)
    return date.replace(year=date.year+nr_of_years)
    

def get_relative_date(rel_string, reference_date = None):
    """returns a date that is calculated relatively to a reference date
    
    :param rel_string: a string like e.g. ``m1y2w3h`` meaning 1 year, 2 weeks and 3 hours ago ("minus")
    :type rel_string: str
    :param reference_date: the reference date, if not given, the current point of time is used
    :type reference_date: :class:`datetime.datetime`
    :return: the date with the relative timespan added
    :rtype: :class:`datetime.datetime`
    """
    if not reference_date:
        reference_date = datetime.datetime.now()
    res = re_rel_date.findall(rel_string)
    if not res:
        return rel_string
    res = res[0]
    sign = res[0]
    dyears = int(res[1][:-1] or 0)
    dmonths = int(res[2][:-1] or 0)
    dweeks = int(res[3][:-1] or 0)
    ddays = int(res[4][:-1] or 0)
    dhours = int(res[5][:-1] or 0)
    
    if USE_DATEUTIL:
        # easy: let dateutil do the heavy lifting
        rel = relativedelta(years=dyears, months=dmonths, days=ddays, weeks=dweeks, hours=dhours)
    else:
        # we have to fallback on timedelta
        if (dmonths):
            # dateutil is not installed, so only years, days, weeks and hours are supported
            # TODO: log a warning
            pass
        rel = datetime.timedelta(days=ddays, weeks=dweeks, hours=dhours)
        if dyears:
            # add years
            rel = add_years(rel, dyears) 
    if sign in ("-", "m"):
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
    if wday_then == None:
        return None
    if wday_now == wday_then:
        # one week later
        print("SAME DAY")
        return reference_date + datetime.timedelta(days = 7)
    elif wday_now > wday_then:
        # next week
        return reference_date + datetime.timedelta(days = (7 - wday_now))
    else:
        # still this week
        return reference_date + datetime.timedelta(days = (wday_then - wday_now))

def to_date(date_string, reference_date = None, prospective = False):
    """ parses a :class:`datetime` object from a given string
    
    :param:`reference_date` may be one of the following:
        * an absolute value like ``today``, ``tomorrow`` or ``2012-07-06``
        * a relative day (``wednesday``, ``+1d``)
    
    :param date_string: a given string representing a (relative) date
    :type date_string: :class:`str`
    :param reference_date: a given date that serves as the reference point for relative date calculations. If ``None``, today's date 00:00am is used.
    :type reference_date: a :class:`datetime` object
    :param prospective: indicates whether a date will rather be put into the future
    :type prospective: bool
    :return: :class:`datetime` object representing the desired date, or if not parsable, the given date string prepended with ``?``
    :rtype: :class:`datetime` or :class:`str`
    """
    if not date_string:
        return None
    now = datetime.datetime.now().replace(second=0, microsecond=0)
    if not reference_date:
        # reference date is today (without hours / min)
        reference_date = datetime.datetime.today()
    # normalize date string
    date_string = date_string.strip().lower()
    date_part = time_part = None
    parts = date_string.split("_", 1)
    if len(parts) == 1:
        date_part, time_part = parts[0], None
    elif len(parts) == 2:
        date_part, time_part = parts
    else:
        date_part, time_part = parts[0:2]
    spec_date = None
    # first handle special cases:
    if date_part in ["now", "n", ""]:
        # absolute: now (without replacing time)
        spec_date = now
    elif date_part in ["today", "td"]:
        # absolute: today (only change day, not time)
        spec_date = reference_date#.replace(hour=reference_date.hour, minute=reference_date.minute)
    elif date_part in ["yesterday", "yday", "yd"]:
        # absolute: yesterday (only change day, not time)
        spec_date = (reference_date + datetime.timedelta(days=-1)).replace(hour=reference_date.hour, minute=reference_date.minute)
    elif date_part in ["tomorrow", "tm"]:
        # absolute: tomorrow (only change day, not time)
        spec_date = (reference_date + datetime.timedelta(days=1)).replace(hour=reference_date.hour, minute=reference_date.minute)
    elif date_part in ["bom", "bm"]:
        # beginning of next month
        spec_date = reference_date.replace(day=1, month=(reference_date.month + 1)% 12, year = reference_date.year + int((reference_date.month + 1) / 12), hour=0, minute=0) 
    elif date_part in ["eom", "em"]:
        # end of this month
        spec_date = reference_date.replace(day=1, month=(reference_date.month + 1)% 12, year = reference_date.year + int((reference_date.month + 1) / 12), hour=0, minute=0) - datetime.timedelta(days=1)
        # TODO: code eom date
    elif date_part in weekdays:
        # a weekday was given
        if prospective:
            pdate = get_date_by_weekday(date_part, now)
        else:
            pdate = get_date_by_weekday(date_part, reference_date)
        spec_date = pdate
    elif re_rel_date.match(date_part):
        # a relative timespan like "-1y5w2d" (1 year, 5 weeks and 2 days)
        if prospective:
            pdate = get_relative_date(date_part, now)
        else:
            pdate = get_relative_date(date_part, reference_date)
        spec_date = pdate
        
    # if time part is existing, update the date accordingly
    if spec_date and time_part:
        if USE_DATEUTIL:
            # try to delegate parsing task to dateutil
            temp_date = parse(time_part, default=reference_date)
        else:
            temp_date = datetime.datetime.strptime(time_part, "%H:%M")
        print(temp_date)
        spec_date = spec_date.replace(hour=temp_date.hour, minute=temp_date.minute)
    
    if spec_date:
        return spec_date
    
    # clean underscores
    if "_" in date_string:
        date_string = date_string.replace("_", " ")

    # try to parse custom date formats
    if hasattr(conf, "date_formats"):
        for date_format in conf.date_formats:
            try:
                # try to parse the custom date formats
                # FIXME: this does not correct shifting dates into the future as below!
                pdate = datetime.datetime.strptime(date_string, date_format.replace("_", " "))
                if pdate.year == 1900:
                    # no year given, the default year is taken
                    pdate = reference_date.replace(month=pdate.month, day=pdate.day, hour=pdate.hour, minute=pdate.minute) 
                return pdate
            except ValueError:
                pass

    try:
        if USE_DATEUTIL:
            # try to delegate parsing task to dateutil
            return parse(date_string, default=reference_date)
        else:
            # try the default date format
            return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M")
    except:
        # date of form xx.xx.
        match = re_partial_date.match(date_string)
        if match:
            month, day = int(match.group(2)), int(match.group(1))
            if month > 12 and day < 12:
                month, day = day, month
            result = datetime.datetime(now.year, month, day)
            # without year, date falls into past -> move to next year
            if now > result:
                # add a year
                result = add_years(result, 1)
            return result

        # show that we could not interpret the date string - return a string
        if not date_string.startswith("?"):
            result = "?" + date_string
        else:
            result = date_string
        return result.replace(" ", "_")


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