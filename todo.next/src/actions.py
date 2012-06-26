"""
:mod:`actions.py`
~~~~~~~~~~~~~~~~~

Contains all actions that can be executed by ``todo.next``

.. created: 26.06.2012
.. moduleauthor:: Phil <Phil@>
"""
from __future__ import print_function
from cli_helpers import ColorRenderer, get_editor_input
from date_trans import to_date

import collections, datetime
from operator import attrgetter


def cmd_list(tl, args):
    """lists all todo items according to a search query
    
    If no search query is given, all items are listed.
    """
    with ColorRenderer() as cr:
        for item in tl.list_items():
            if not args.search_string or args.search_string in item.text:
                print(cr.render(item))
                #print(item)


def cmd_add(tl, args):
    """
    """
    with ColorRenderer() as cr:
        if not args.text:
            # no arguments given, open editor and let user enter data there
            # TODO: insert via editor
            pass
        elif isinstance(args.text, list):
            # string not enclosed in ""
            item = tl.add_item(" ".join(args.text))
        else:
            # single string 
            item = tl.add_item(args.text)
        print("Added", cr.render(item))

def cmd_remove(tl, args):
    with ColorRenderer() as cr:
        item_list = []
        for item_nr in args.items:
            item_list.append(tl.get_item_by_index(item_nr))
        if not args.force:
            print("Do you really want to remove the following item(s):")
            for item in item_list:
                print(cr.render(item))
            answer = raw_input("Please confirm (y/N): ").lower().strip()
            if answer == "y":
                for item in item_list:
                    tl.remove_item(item)
            else:
                print("Removing aborted")
        else:
            for item in item_list:
                tl.remove_item(item)
    
def cmd_done(tl, args):
    with ColorRenderer() as cr:
        item_list = []
        for item_nr in args.items:
            item_list.append(tl.get_item_by_index(item_nr))
        print("Marked following todo items as 'done':")
        for item in item_list:
            tl.set_to_done(item)
            print(cr.render(item))

def cmd_reopen(tl, args):
    with ColorRenderer() as cr:
        item_list = []
        for item_nr in args.items:
            item_list.append(tl.get_item_by_index(item_nr))
        print("Setting the following todo items to open again:")
        for item in item_list:
            tl.reopen(item)
            print(cr.render(item))
    
def cmd_agenda(tl, args):
    with ColorRenderer() as cr:
        agenda_items = []
        # if not set, get agenda for today
        if not args.date:
            args.date = datetime.datetime.now()
        else:
            args.date = to_date(args.date)
            if isinstance(args.date, basestring):
                print("Could not parse date argument '%s'" % args.date)
                quit(-1)
        for item in tl.list_items():
            comp_date = item.due_date
            if comp_date:
                if (args.date.year, args.date.month, args.date.day) == (comp_date.year, comp_date.month, comp_date.day):
                    agenda_items.append(item)
        agenda_items.sort(key=attrgetter("due_date"))
        for item in agenda_items:
            print(cr.render(item))

def cmd_edit(tl, args):
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        print(cr.render(item))
        try:
            output = get_editor_input(item.text)
            # remove new lines
            item.text = output.replace("\n", " ")
            tl.reparse_item(item)
            print(cr.render(item))
        except KeyboardInterrupt:
            # editing has been aborted
            pass

def cmd_delegated(tl, args):
    with ColorRenderer() as cr:
        to_list = collections.defaultdict(list)
        for item in tl.list_items():
            for delegate in item.delegated_to:
                to_list[delegate.lower()].append(item)
        if args.delegate:
            if args.delegate.lower() in to_list:
                print("Delegated to", args.delegate)
                for item in sorted(to_list[args.delegate.lower()], cmp=tl.default_sort):
                    print(cr.render(item))
            else:
                print("No items have been found delegated to", args.delegate)
        else:
            for delegate in sorted(to_list.keys()):
                print("Delegated to", delegate)
                for item in sorted(to_list[delegate], cmp=tl.default_sort):
                    print(cr.render(item))

def cmd_tasked(tl, args):
    with ColorRenderer() as cr:
        from_list = collections.defaultdict(list)
        for item in tl.list_items():
            for delegate in item.delegated_from:
                from_list[delegate.lower()].append(item)
        if args.initiator:
            if args.initiator.lower() in from_list:
                print("Tasks from", args.initiator)
                for item in sorted(from_list[args.initiator.lower()], cmp=tl.default_sort):
                    print(cr.render(item))
            else:
                print("No tasks have been given to you :)", args.initiator)
        else:
            for delegate in sorted(from_list.keys()):
                print("Tasks from", delegate)
                for item in sorted(from_list[delegate], cmp=tl.default_sort):
                    print(cr.render(item))


def cmd_delay(tl, args):
    raise NotImplementedError()

def cmd_overdue(tl, args):
    raise NotImplementedError()

def cmd_report(tl, args):
    raise NotImplementedError()

def cmd_archive(tl, args):
    raise NotImplementedError()

def cmd_clean(tl, args):
    raise NotImplementedError()

def cmd_stats(tl, args):
    # TODO: write # open / # done / # prioritized / # overdue items
    raise NotImplementedError()

def cmd_open(tl, args):
    raise NotImplementedError()

def cmd_project(tl, args):
    raise NotImplementedError()

def cmd_context(tl, args):
    raise NotImplementedError()