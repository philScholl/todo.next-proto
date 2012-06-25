"""
:mod:``
~~~~~~~~~~~~~~~~~~~~~



.. created: 25.06.2012
.. moduleauthor:: Phil <Phil@>
"""
from __future__ import print_function
import datetime, re
from dateutil.parser import parse

re_partial_date = re.compile("(\d{1,2})\.(\d{1,2})\.", re.UNICODE)

def to_date(date_string):
    if not date_string:
        return None
    date_string = date_string.strip().lower()
    now = datetime.datetime.now()
    if date_string in ["today", "td", ""]:
        return datetime.datetime(now.year, now.month, now.day)
    elif date_string in ["tomorrow", "tm"]:
        return datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
    # clean underscores
    if "_" in date_string:
        date_string = date_string.replace("_", " ")
    try:
        # try to delegate parsing task to dateutil
        default = datetime.datetime(now.year, now.month, now.day)
        return parse(date_string, default=default)
    except:
        # date of form xx.xx.
        match = re_partial_date.match(date_string)
        if match:
            month, day = int(match.group(2)), int(match.group(1))
            if month > 12 and day < 12:
                month, day = day, month
            result = datetime.datetime(now.year, month, day)
            if now > result:
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