"""
:mod:`todoitem`
~~~~~~~~~~~~~~~

Provides functionality for a single todo item

.. todo:: ``created`` flag handling due to todo.txt syntax

.. created: 25.06.2012
.. moduleauthor:: Phil <Phil@>
"""
from __future__ import print_function
import parsers
from date_trans import from_date, to_date, is_same_day
import datetime, re

class TodoItem(object):
    def __init__(self, item_text):
        self.text = item_text
        self.properties = {}
        self.urls = []
        self.priority = None
        self.delegated_to, self.delegated_from = [], []
        self.projects, self.contexts = [], []
        self.done = None
        self.is_report = None
        self.nr = None
        # find all special syntax
        self.parse()
        # fix dates on properties
        self.fix_properties()
    
    def set_date(self, prop_name, date_or_str):
        if isinstance(date_or_str, basestring):
            self.properties[prop_name] = to_date(date_or_str)
        elif isinstance(date_or_str, (datetime.date, datetime.datetime)):
            self.properties[prop_name] = date_or_str
        elif date_or_str == None:
            self.properties[prop_name] = None
        else:
            print("ERROR: setting non-date or non-string")

    def get_date(self, prop_name):
        return self.properties.get(prop_name, None)

    def set_due_date(self, date_or_str):
        self.set_date("due", date_or_str)

    def get_due_date(self):
        return self.get_date("due")
    
    def set_done_date(self, date_or_str):
        self.set_date("done", date_or_str)
        
    def get_done_date(self):
        return self.get_date("done")
    
    def set_created_date(self, date_or_str):
        self.set_date("created", date_or_str)
    
    def get_created_date(self):
        return self.get_date("created")
    
    due_date = property(fget = get_due_date, fset = set_due_date)
    done_date = property(fget = get_done_date, fset = set_done_date)
    created_date = property(fget = get_created_date, fset = set_created_date)
    
    def is_overdue(self, reference_date = None):
        if not reference_date:
            reference_date = datetime.datetime.now()
        if self.due_date and reference_date > self.due_date:
            if (self.due_date.hour, self.due_date.minute) == (0, 0) and is_same_day(self.due_date, reference_date):
                return False
            else:
                return True
        return False
    
    
    def is_still_open_today(self, reference_date = None):
        if self.due_date:
            if not reference_date:
                reference_date = datetime.datetime.now()
            if is_same_day(self.due_date, reference_date):
                if (self.due_date.hour, self.due_date.minute) == (0, 0): 
                    # is due today on general day
                    return True
                elif self.due_date > reference_date:
                    # due date is today but will be later on
                    return True
                else:
                    # due date has already happened today
                    return False
        return False
    
    
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
        # replace ``done`` properties with current value (and add datetime object for properties)
        self.replace_or_add_prop("done", from_date(now), now)
        # add marker "x " at beginning
        if not self.text.startswith("x "):
            self.text = "x " + self.text

    def replace_or_add_prop(self, property_name, new_property_value, real_property_value = None):
        if real_property_value:
            self.properties[property_name] = real_property_value
        else:
            self.properties[property_name] = new_property_value
        re_replace_prop = re.compile(r"\b(%s:.+?)(?:$|\s)" % property_name, re.UNICODE)
        matches = re_replace_prop.findall(self.text)
        if len(matches) > 0:
            # only replace the first occurrence
            self.text = self.text.replace(matches[0], "%s:%s" % (property_name, new_property_value))
            # and remove all further occurrences
            for match in matches[1:]:
                self.text = self.text.replace(match, "")
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
        for prop_name in props:
            if "%s:" % prop_name not in self.text:
                # we need to normalize this property name, make everything lowercase
                re_normalize_prop = re.compile("(%s:)" % prop_name, re.IGNORECASE)
                self.text = re_normalize_prop.sub("%s:" % prop_name, self.text)
            if prop_name in date_props:
                # replace all date props with a "beautified" date string
                repl_date = to_date(props[prop_name])
                if repl_date:
                    self.text = self.text.replace(props[prop_name], from_date(repl_date))
                    props[prop_name] = repl_date