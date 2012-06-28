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
    USE_DATEUTIL = True
except ImportError:
    pass

re_partial_date = re.compile("(\d{1,2})\.(\d{1,2})\.", re.UNICODE)

def is_same_day(date1, date2):
    return (date1.year, date1.month, date1.day) == (date2.year, date2.month, date2.day)

def shorten_date(date, today = None):
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
        reference_date = datetime.datetime(now.year, now.month, now.day)
    date_string = date_string.strip().lower()
    if date_string in ["today", "td", ""]:
        return reference_date
    elif date_string in ["tomorrow", "tm"]:
        return reference_date + datetime.timedelta(days=1)
    # clean underscores
    if "_" in date_string:
        date_string = date_string.replace("_", " ")
    try:
        if USE_DATEUTIL:
            # try to delegate parsing task to dateutil
            return parse(date_string, default=reference_date)
        else:
            # FIXME: fix format string
            return datetime.datetime.strptime(date_string, "format")
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