"""
.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function

from date_trans import from_date
from todoitem import TodoItem
import codecs
import datetime

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
    
    
    def write(self):
        with codecs.open(self.todofile, "w", "utf-8") as fp:
            if not self.sorted:
                self.sort_list()
            for item in self.todolist:
                fp.write("%s\n" % item.text)
    
    
    def append(self, item_str):
        item_str = item_str.strip()
        if not item_str:
            return
        item = TodoItem(item_str)
        self.todolist.append(item)
        self.sorted = False
        return item


    def add_item(self, item_str):
        item = self.append(item_str)
        if item.is_report:
            # in case of report item, we need to store the "done" date for later sorting
            item.replace_or_add_prop("done", from_date(datetime.datetime.now()))
        self.dirty = True
        return item
    

    def set_to_done(self, item):
        # report items cannot be marked as done, as they are "done" by definition
        if item.is_report:
            return item
        item.set_to_done()
        self.sorted = False
        self.dirty = True
        return item


    def reopen(self, item):
        item.reopen()
        self.dirty = True
        self.sorted = False
        return item
    
    
    def get_item_by_index(self, item_nr):
        item = self.todolist[item_nr]
        item.nr = int(item_nr)
        return item
    
    
    def remove_item(self, item):
        self.todolist.remove(item)
        self.dirty = True
    
    
    def reparse_item(self, item):
        item.parse()
        item.fix_properties()
        self.sorted = False
        self.dirty = True
        
        
    def sort_key_by(self, property_name, default):
        def inner_getter(item):
            if not property_name in item.properties:
                return default
            else:
                return item.properties[property_name]
        return inner_getter
       
    
    def default_sort(self, item1, item2):
        # sort whether report item (they are right at the bottom)
        if item1.is_report and not item2.is_report:
            return 1
        if not item1.is_report and item2.is_report:
            return -1
        # sort by done
        if item1.done and not item2.done:
            return 1
        elif not item1.done and item2.done:
            return -1
        # sort by priority
        i1, i2 = (item1.priority or "ZZ"), (item2.priority or "ZZ")
        if i1 > i2:
            return 1
        elif i1 < i2:
            return -1
        # sort alphabetically
        i1, i2 = item1.text.lower(), item2.text.lower()
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
            item.nr = nr
            yield item