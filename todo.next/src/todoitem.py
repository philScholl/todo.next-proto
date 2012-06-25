"""
:mod:``
~~~~~~~~~~~~~~~~~~~~~



.. created: 25.06.2012
.. moduleauthor:: Phil <Phil@>
"""
from __future__ import print_function
import parsers
from date_trans import from_date, to_date
import datetime, re

class TodoItem(object):
    def __init__(self, item_text):
        self.text = item_text
        self.properties = {}
        self.priority = None
        self.delegated_to, self.delegated_from = [], []
        self.projects, self.contexts = [], []
        self.done = None
        self.is_report = None
        # find all special syntax
        self.parse()
        # fix dates on properties
        self.fix_properties()

    def set_due_date(self, date_or_str):
        if isinstance(date_or_str, basestring):
            self.properties["due"] = to_date(date_or_str)
        elif isinstance(date_or_str, (datetime.date, datetime.datetime)):
            self.properties["due"] = date_or_str
        elif date_or_str == None:
            self.properties["due"] = None
        else:
            print("ERROR: setting non-date or non-string")

    def get_due_date(self):
        return self.properties.get("due", None)
    
    due_date = property(fget = get_due_date, fset = set_due_date)
    
    def reopen(self):
        self.done = False
        # remove "x " prefix
        if self.text.startswith("x "):
            self.text = self.text[2:]
    
    def set_to_done(self):
        # set to done
        self.done = True
        # if necessary, create properties
        now = datetime.datetime.now()
        self.properties["done"] = now
        # replace ``done`` properties with current value
        self.replace_or_add_prop("done", from_date(now))
        # add marker "x " at beginning
        if not self.text.startswith("x "):
            self.text = "x " + self.text

    def replace_or_add_prop(self, property_name, new_property_value):
        self.properties[property_name] = new_property_value
        re_replace_prop = re.compile("(?:^|\s)(%s:.*?)(?:$|\s)" % property_name, re.UNICODE)
        matches = re_replace_prop.findall(self.text)
        if len(matches) > 0:
            # only replace the first occurrence
            self.text = self.text.replace(matches[0], "%s:%s" % (property_name, new_property_value))
            # and remove all further occurrences
            for _match in matches[1:]:
                self.text = self.text.replace(matches[0], "")
        else:
            self.text = self.text.strip() + " %s:%s" % (property_name, new_property_value)

    def parse(self):
        parse_fns = dir(parsers)
        for p in parse_fns:
            if p.startswith("parse"):
                getattr(parsers, p)(self)

    def fix_properties(self):
        props = self.properties
        date_props = ["due", "done", "created"]
        # fix properties, if possible
        for prop_name in date_props:
            if prop_name in props:
                repl_date = to_date(props[prop_name])
                if repl_date:
                    self.text = self.text.replace(props[prop_name], from_date(repl_date))
                    props[prop_name] = repl_date