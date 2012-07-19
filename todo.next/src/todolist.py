"""
.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function

from date_trans import from_date
from todoitem import TodoItem
from config import ConfigBorg

import datetime, codecs, hashlib, random, math, sys
from itertools import groupby

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)
DEFAULT_LEN = 3

conf = ConfigBorg()

class TodoList(object):
    """class representing a todo list that's stored in a ``todo.next`` file.
    """
    
    def __init__(self, todofile):
        """constructor, reads file and fills todo list with :class:`TodoItem`s
        
        :param todofile: the filename of the ``todo.next`` file
        :type todofile: str
        """
        self.todofile = todofile
        self.todolist = []
        self.tids = {}
        self.dirty = False
        self.dependencies = {}
        
        if conf.id_support:
            # initialize randomizer for tid generation
            random.seed()
        # read todo file items
        with codecs.open(self.todofile, "r", "utf-8") as fp:
            for line_nr, line in enumerate(fp):
                line = line.strip()
                if not line:
                    continue
                # append items to list
                item = self._append(line)
                if item.tid:
                    if item.tid in self.tids:
                        # duplicate ID - what to do now?
                        # TODO: log that as a warning
                        pass
                    else:
                        self.tids[item.tid] = item
                # build blockedby dependencies
                if conf.id_support and conf.BLOCKEDBY in item.properties and item.tid and not (item.done or item.is_report):
                    tids = item.properties[conf.BLOCKEDBY]
                    self.dependencies[item.tid] = tids
                # set line number in file
                item.line_nr = line_nr
        self.clean_dependencies()
        # sort list
        self.sort_list()
    
    
    def __enter__(self):
        """context manager: on entering returns this :class:`TodoList`
        
        :returns: the todo list object
        :rtype: :class:`TodoList`
        """
        return self
    
    
    def __exit__(self, exc_type, exc_val, exc_tb): #@UnusedVariable
        """context manager: on closing, writes the altered todo file
        
        :param exc_type: exception type
        :type exc_type: ?
        :param exc_val: exception value
        :type exc_val: ?
        :param exc_tb: the exception's traceback
        :type exc_tb: ?
        :returns: whether the exception was handled in here
        :rtype: bool
        """
        # if we have changed something, we need to write these changes to file again
        if self.dirty:
            if exc_type:
                # we encountered an exception, check whether we accidentally removed anything
                print("ERROR: An error occurred, thus the changes have not been saved (you don't want to lose your data)!")
            else:
                #print("would write")
                self.write()
        # we don't swallow the exceptions
        return False

    
    def write(self):
        """writes the todo items back to the file
        """
        with codecs.open(self.todofile, "w", "utf-8") as fp:
            if conf.sort and not self.sorted:
                # sort list according to own rules
                self.sort_list()
            elif not conf.sort:
                # sort list according to original order (line number in todo.txt file)
                self.todolist.sort(key=lambda x: x.line_nr if x.line_nr != None else sys.maxint)
            for item in self.todolist:
                fp.write("{item_str}\n".format(item_str = item.text))
    
    
    def _append(self, item_str):
        """appends a todo item to the todo list
        
        :param item_str: the string representation of a :class:`TodoItem`
        :type item_str: str
        :returns: the parsed todo item
        :rtype: :class:`TodoItem` 
        """
        item_str = item_str.strip()
        if not item_str:
            return
        item = TodoItem(item_str)
        self.todolist.append(item)
        self.sorted = False
        return item


    def clean_dependencies(self, done = None):
        # an item has been marked as done or removed, remove as blockedby in dependency
        if done and done.tid:
            for item_id, deps in self.dependencies.items():
                # if it has been found as a block for other items
                if done.tid in deps:
                    # update the dependencies
                    self.dependencies[item_id].remove(done.tid)
        # check dependencies for non-existing blocks
        for item_id, deps in self.dependencies.items():
            for tid in deps:
                # get item
                item = self.get_item_by_index(tid)
                if tid not in self.tids or item.done:
                    # blocked item is not existing anymore
                    # print("ID '{item_id}' blocks '{block_id}' but is not existing anymore".format(item_id = tid, block_id = item_id))
                    item = self.tids[item_id]
                    self.replace_or_add_prop(item, conf.BLOCKEDBY, None, tid)
                    self.dirty = True

    
    def create_tid(self, item, maxlen = DEFAULT_LEN):
        """creates a random :var:`DEFAULT_LEN`-letter tid
        
        :param item: a todo item
        :type item: :class:`TodoItem`
        :return: a :var:`DEFAULT_LEN`-letter tid
        :rtype: str 
        """
        # set first value
        text = item.text
        counter = 0
        # try at most 60 times
        while counter < 60:
            # for generating different tids for same text
            salt = random.choice(ALPHABET)
            text = salt + text
            # get hash
            md5 = hashlib.new("md5", text)
            # maximal number that needs to be reachable for maxlen characters
            max_nr = len(ALPHABET) ** maxlen
            # maximal size of the the hex string to be able to represent this number
            len_hex_str = int(math.ceil(math.log(max_nr, 16)))
            # get base-26 DEFAULT_LEN-digit nr
            nr = int(md5.hexdigest()[:len_hex_str], 16) % max_nr
            
            # get base-26 representation of nr
            char_list = []
            t = maxlen - 1
            # transform nr in base of alphabet
            while t >= 0:
                bcp = int(pow(BASE, t))
                a = int(nr / bcp) % BASE
                char_list.append(ALPHABET[a:a+1])
                nr = nr - (a * bcp)
                t -= 1
            
            tid = "".join(char_list)
            if tid not in self.tids:
                return tid
            counter += 1
        # we tried often enough and failed :(
        return "xxx"


    def add_item(self, item_str):
        """exposed add item method, adds a new todo item to the todo file and reindexes
        
        :param item_str: the string representation of a :class:`TodoItem`
        :type item_str: str
        :returns: the parsed todo item
        :rtype: :class:`TodoItem` 
        """
        # append the item to the todo list
        item = self._append(item_str)
        # add done and created properties
        now = datetime.datetime.now()
        now_str = from_date(now)
        if item.is_report:
            # in case of report item, we need to store the "done" date for later sorting
            item.replace_or_add_prop(conf.DONE, now_str, now)
        else:
            item.replace_or_add_prop(conf.CREATED, now_str, now)
        # if item doesn't have an tid assigned, do it here automatically
        if conf.id_support and not item.tid:
            item_id = self.create_tid(item)
            item.replace_or_add_prop(conf.ID, item_id)
            self.tids[item_id] = item
        # add to dependencies
        if conf.id_support and item.tid and conf.BLOCKEDBY in item.properties:
            self.dependencies[item.tid] = item.properties[conf.BLOCKEDBY]
        # the new item is sorted into the list
        self.reindex()
        # something has changed
        self.dirty = True
        return item
    

    def check_items(self):
        """checks all items for potential syntax problems, e.g. non-existing files 
        and unparsable dates
        
        :return: generator, yield tuple ``(item, warnings)``
        :rtype: yields (item, list(str))
        """
        tids = []
        for item in self.list_items():
            if item.tid:
                tids.append((item.tid, item))
            warnings = item.check(False)
            if warnings:
                yield (item, warnings)
        if conf.id_support:
            # check for duplicate tids
            for item_id, group in groupby(tids, key=lambda x: x[0]):
                group = [item for _, item in group]
                if len(group) > 1:
                    for item in group:
                        yield (item, ["Item has duplicate ID '{item_id}'".format(item_id = item_id),])                    


    def remove_prop(self, item, property_name, selector_value = None):
        item.remove_prop(property_name, selector_value)
        self.reindex()
        self.dirty = True
        return item
        
    
    def replace_or_add_prop(self, item, prop_name, new_prop_val, real_prop_val = None):
        """replaces a property in the item text or, if already existent, updates it.
        
        .. note:: the properties are considered to be unique, i.e. only one property
                  of a certain name may exist.
                  
        :param item: a todo item
        :type item: :class:`TodoItem`
        :param prop_name: the name of the property to be changed (e.g. "done")
        :type prop_name: str
        :param new_prop_val: the new property value in string form (e.g. "2012-07-02"). 
            If ``None``, the property will be deleted.
        :type new_prop_val: str
        :param real_prop_val: an object representation of the property value, e.g. a 
            :class:`datetime.datetime` object representing the date of the value that
            the properties field will contain. If not set, the string value is taken.
            Special semantics: If ``new_prop_val`` is ``None``, this acts as a 
            selector, removing only the parameter that has this value.
        :type real_prop_val: any
        :returns: the altered todo item
        :rtype: :class:`TodoItem` 
        """
        item.replace_or_add_prop(prop_name, new_prop_val, real_prop_val)
        self.reindex()
        self.dirty = True
        return item


    def set_to_done(self, item):
        """sets the state of a :class:`TodoItem` to *done*.
        
        The ``done`` flag and the done date are set.
        
        :param item: a todo item
        :type item: :class:`TodoItem`
        :returns: the altered todo item
        :rtype: :class:`TodoItem` 
        """
        # report items cannot be marked as done, as they are "done" by definition
        if item.is_report:
            return item
        item.set_to_done()
        # clean blockedby dependencies
        self.clean_dependencies(done=item)
        # reindex the list, as the order may have changed
        self.reindex()
        self.dirty = True
        return item


    def reopen(self, item):
        """sets the state of a :class:`TodoItem` to *not done*.
        
        Only the ``done`` flag is reset, the done date stays for 
        reporting reasons (may change).
        
        :param item: a todo item
        :type item: :class:`TodoItem`
        :returns: the altered todo item
        :rtype: :class:`TodoItem` 
        """
        # report items cannot be marked as undone, as they are "done" by definition
        if item.is_report:
            return item
        item.reopen()
        self.dirty = True
        self.reindex()
        return item
    
    
    def get_item_by_index(self, item_nr):
        """returns the ``n-th`` todo item from the todo list
        
        :param item_nr: the index of the requested item
        :type item_nr: str
        :returns: the requested todo item (if existing)
        :rtype: :class:`TodoItem` 
        """
        # if list is unsorted, do that first
        if not self.sorted:
            self.sort_list()
        try:
            if conf.id_support and item_nr in self.tids:
                item = self.tids[item_nr]
                item.nr = self.todolist.index(item)
            else:
                item_nr = int(item_nr)
                # simply look up the index
                item = self.todolist[item_nr]
                # assign the index temporarily
                item.nr = item_nr
        except:
            return None
        return item
    
    
    def get_items_by_index_list(self, item_nrs):
        """returns a list of todo items from the todo list by indices
        
        :param item_nrs: an iterable of the indices of the requested items
        :type item_nr: list(str)
        :returns: the requested todo items (if existing)
        :rtype: list(:class:`TodoItem`) 
        """
        ret = []
        for item_nr in item_nrs:
            item = self.get_item_by_index(item_nr)
            if item:
                ret.append(item) 
        return ret
    
    
    def remove_item(self, item):
        """removes a todo item from the todo list
        
        :param item: the todo item to be removed
        :type item: :class:`TodoItem`
        :return: the removed item
        :rtype: :class:`TodoItem`
        """
        self.todolist.remove(item)
        item.nr = None
        self.clean_dependencies(item)
        self.reindex()
        self.dirty = True
        return item
    
    
    def replace_item(self, item, new_item):
        """replaces a todo item in the todo list with another item
        
        :param item: the old todo item to be replaced
        :type item: :class:`TodoItem`
        :param new_item: the new todo item to replace the old one
        :type new_item: :class:`TodoItem`
        :return: the new item
        :rtype: :class:`TodoItem`
        """
        # set to index and copy index number
        index = self.todolist.index(item)
        new_item.nr = index
        self.todolist[index] = new_item
        # line number
        new_item.line_nr = item.line_nr
        self.clean_dependencies()
        self.reindex()
        self.dirty = True
        return new_item
        
        
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
            item.text = "({prio}) {item_str}".format(prio = new_prio, item_str = item.text)
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