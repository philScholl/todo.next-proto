"""
.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function

import codecs
import parsers
import datetime
from dateutil.parser import parse
import re

re_partial_date = re.compile("(\d{1,2})\.(\d{1,2})\.", re.UNICODE)

class TodoList(object):
    def __init__(self, todofile):
        self.todofile = todofile
        self.todolist = []
        self.dirty = False
        # read todo file items
        with codecs.open(self.todofile, "r", "utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                self.append(line)
        self.sort_list()
                
    def parse(self, item):
        parse_fns = dir(parsers)
        for p in parse_fns:
            if p.startswith("parse"):
                getattr(parsers, p)(item)
    
    def write(self):
        with codecs.open(self.todofile, "w", "utf-8") as fp:
            if not self.sorted:
                self.sort_list()
            for item in self.todolist:
                fp.write("%s\n" % item["raw"])
    
    
    def append(self, item_str):
        item_str = item_str.strip()
        if not item_str:
            return
        item = {}
        item["raw"] = item_str
        # find all special syntax
        self.parse(item)
        # fix dates on properties
        self.fix_properties(item)
        self.todolist.append(item)
        self.sorted = False
        return item

    def add_item(self, item_str):
        item = self.append(item_str)
        if item.get("reportitem", False):
            # in case of report item, we need to store the "done" date for later sorting
            # TODO: add "done" flag with current date
            pass
        self.dirty = True
        return item

    def set_to_done(self, item):
        item["done"] = True
        # is ``done`` property already in here
        props = item.get("properties", None)
        if not props:
            item["properties"] = {}
        now = datetime.datetime.now()
        props["done"] = now
        done = self.from_date(now)
        re_replace_prop = re.compile("(?:^|\s)(done:.*?)(?:$|\s)", re.UNICODE)
        matches = re_replace_prop.findall(item["raw"])
        if len(matches) > 0:
            # only replace the first occurrence
            item["raw"] = item["raw"].replace(matches[0], "done:" + done)
            # and remove all further occurrences
            for _match in matches [1:]:
                item["raw"] = item["raw"].replace(matches[0], "")
        else:
            item["raw"] = item["raw"].strip() + " " + "done:" + done
        if not item["raw"].startswith("x "):
            item["raw"] = "x " + item["raw"]
        self.sorted = False
        self.dirty = True
        return item

    def reopen(self, item):
        item["done"] = False
        # remove "x " prefix
        if item["raw"].startswith("x "):
            item["raw"] = item["raw"][2:]
        self.dirty = True
        self.sorted = False
        return item
    
    def get_item_by_index(self, item_nr):
        item = self.todolist[item_nr]
        item["nr"] = int(item_nr)
        return item
        
    def remove_item(self, item):
        self.todolist.remove(item)
        self.dirty = True
    
    def from_date(self, date):
        if isinstance(date, basestring):
            return date
        else:
            return date.strftime("%Y-%m-%d_%H:%M")
    
    def to_date(self, date_string):
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
            default = datetime.datetime(now.year, now.month, now.day, now.hour)
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
    
    
    def fix_properties(self, item):
        props = item.get("properties", {})
        date_props = ["due", "done"]
        # fix properties, if possible
        for prop_name in date_props:
            if prop_name in props:
                repl_date = self.to_date(props[prop_name])
                item["raw"] = item["raw"].replace(props[prop_name], self.from_date(repl_date))
                props[prop_name] = repl_date
                
    
    def default_sort(self, item1, item2):
        # sort whether report item (they are right at the bottom)
        i1, i2 = item1.get("reportitem", False), item2.get("reportitem", False)
        if i1 and not i2:
            return 1
        if not i1 and i2:
            return -1
        # sort by done
        i1, i2 = item1["done"], item2["done"]
        if i1 and not i2:
            return 1
        elif not i1 and i2:
            return -1
        # sort by priority
        i1, i2 = item1.get("priority", "ZZ"), item2.get("priority", "ZZ")
        if i1 > i2:
            return 1
        elif i1 < i2:
            return -1
        # sort alphabetically
        i1, i2 = item1["raw"].lower(), item2["raw"].lower()
        if i1 > i2:
            return 1
        elif i1 < i2:
            return -1
        # they are practically equal
        return 0
    
    
    def sort_list(self, sorting_fn = None):
        if sorting_fn == None:
            sorting_fn = self.default_sort
        self.todolist.sort(cmp=sorting_fn)
        self.sorted = True
    
    
    def list_items(self):
        if not self.sorted:
            self.sort_list()
        for nr, item in enumerate(self.todolist):
            item["nr"] = nr
            yield item