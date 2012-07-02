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
    
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb): #@UnusedVariable
        # if we have changed something, we need to write these changes to file again
        if self.dirty:
            #print("would write")
            self.write()
        # we don't swallow the exceptions
        return False

    
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
        now_str = from_date(datetime.datetime.now())
        if item.is_report:
            # in case of report item, we need to store the "done" date for later sorting
            item.replace_or_add_prop("done", now_str)
        else:
            item.replace_or_add_prop("created", now_str)
        self.reindex()
        self.dirty = True
        return item
    

    def replace_or_add_prop(self, item, prop_name, new_prop_val, real_prop_val = None):
        item.replace_or_add_prop(prop_name, new_prop_val, real_prop_val)
        self.reindex()
        self.dirty = True
        return item


    def set_to_done(self, item):
        # report items cannot be marked as done, as they are "done" by definition
        if item.is_report:
            return item
        item.set_to_done()
        self.reindex()
        self.dirty = True
        return item


    def reopen(self, item):
        item.reopen()
        self.dirty = True
        self.reindex()
        return item
    
    
    def get_item_by_index(self, item_nr):
        if not self.sorted:
            self.sort_list()
        item = self.todolist[item_nr]
        item.nr = int(item_nr)
        return item
    
    
    def get_items_by_index_list(self, item_nrs):
        return [self.get_item_by_index(item_nr) for item_nr in item_nrs]
    
    def remove_item(self, item):
        self.todolist.remove(item)
        self.reindex()
        self.dirty = True
    
    
    def replace_item(self, item, new_item):
        index = self.todolist.index(item)
        new_item.nr = index
        self.todolist[index] = new_item
        self.reindex()
        self.dirty = True
        
        
    def sort_key_by(self, property_name, default):
        def inner_getter(item):
            if not property_name in item.properties:
                return default
            else:
                return item.properties[property_name]
        return inner_getter
       
    def set_priority(self, item, new_prio):
        if new_prio:
            if item.priority:
                # slice off the old prio
                item.text = item.text[4:]
            # prepend the new prio
            item.text = "(%s) %s" % (new_prio, item.text)
        else:
            # remove priority flag
            if item.priority:
                # remove "(x) " at beginning
                item.text = item.text[4:]
        item.priority = new_prio
        self.reindex()
        self.dirty = True
    
    def default_sort(self, item1, item2):
        # sort whether report item (they are right at the bottom)
        i1, i2 = (item1.is_report or item1.done), (item2.is_report or item2.done)
        if i1 and not i2:
            return 1
        if not i1 and i2:
            return -1
#        if item1.is_report and not item2.is_report:
#            return 1
#        if not item1.is_report and item2.is_report:
#            return -1
#        # sort by done
#        if item1.done and not item2.done:
#            return 1
#        elif not item1.done and item2.done:
#            return -1
        # sort by priority
        i1, i2 = (item1.priority or "ZZ"), (item2.priority or "ZZ")
        if i1 > i2:
            return 1
        elif i1 < i2:
            return -1
        # sort by reversed done date
        (i1, i2) = (item1.done_date if isinstance(item1.done_date, datetime.datetime) else datetime.datetime(1970, 1, 1), 
                    item2.done_date if isinstance(item2.done_date, datetime.datetime) else datetime.datetime(1970, 1, 1))
        if i1 < i2:
            return 1
        if i1 > i2:
            return -1
        # sort by reversed due date
        (i1, i2) = (item1.due_date if isinstance(item1.due_date, datetime.datetime) else datetime.datetime(1970, 1, 1), 
                    item2.due_date if isinstance(item2.due_date, datetime.datetime) else datetime.datetime(1970, 1, 1))
        if i1 < i2:
            return 1
        if i1 > i2:
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
    
    
    def reindex(self):
        self.sort_list()
        for nr, item in enumerate(self.todolist):
            item.nr = nr 
    

    def list_items(self, criterion_fn = None):
        # we need to get the list sorted
        if not self.sorted:
            self.sort_list()
        # loop through all items
        for nr, item in enumerate(self.todolist):
            # attach number according to index
            item.nr = nr
            if criterion_fn:
                # if a criterion is defined, use it to determine whether to return item
                if criterion_fn(item):
                    yield item
            else:
                # just return every item
                yield item