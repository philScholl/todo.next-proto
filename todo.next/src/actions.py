"""
:mod:`actions.py`
~~~~~~~~~~~~~~~~~

Contains all actions that can be executed by ``todo.next``

.. created: 26.06.2012
.. moduleauthor:: Phil <Phil@>
"""
from __future__ import print_function
from cli_helpers import ColorRenderer, get_editor_input, open_editor
from date_trans import to_date, is_same_day

import collections, datetime, re, os
from operator import attrgetter
from itertools import groupby
import webbrowser


def get_oneliner(func):
    try:
        return func.__doc__.split("\n")[0].strip()
    except:
        return "n/a"


def cmd_list(tl, args):
    """lists all items that match the given expression
    
    If no search query is given, all items are listed.
    """
    with ColorRenderer(args) as cr:
        if args.regex:
            if not args.search_string:
                # does not make sense
                args.regex = False
            re_search = re.compile(args.search_string, re.UNICODE)
        for item in tl.list_items():
            if not args.all and (item.is_report or item.done):
                continue
            if args.regex:
                if re_search.findall(item.text):
                    print(cr.render(item))
            elif not args.search_string or args.search_string in item.text: 
                print(cr.render(item))


def cmd_add(tl, args):
    """adds a new todo item to the todo list
        
    The source of the todo item can either be the command line or an editor.
    """
    with ColorRenderer() as cr:
        if not args.text:
            # no arguments given, open editor and let user enter data there
            output = get_editor_input("")
            item = tl.add_item(output.replace("\r\n", " ").replace("\n", " ").strip())
            pass
        elif isinstance(args.text, list):
            # string not enclosed in ""
            item = tl.add_item(" ".join(args.text))
        else:
            # single string 
            item = tl.add_item(args.text)
        print("Added", cr.render(item))


def cmd_remove(tl, args):
    """removes one or more items from the todo list
    """
    with ColorRenderer() as cr:
        item_list = [tl.get_item_by_index(item_nr) for item_nr in args.items]
        if not args.force:
            print("Do you really want to remove the following item(s):")
            for item in item_list:
                print(" ", cr.render(item))
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
    """sets the status of one or more todo items to 'done'
    """
    with ColorRenderer() as cr:
        item_list = [tl.get_item_by_index(item_nr) for item_nr in args.items]
        print("Marked following todo items as 'done':")
        for item in item_list:
            tl.set_to_done(item)
            print(" ", cr.render(item))


def cmd_reopen(tl, args):
    """reopens one or more items marked as 'done'
    """
    with ColorRenderer() as cr:
        item_list = [tl.get_item_by_index(item_nr) for item_nr in args.items]
        print("Setting the following todo items to open again:")
        for item in item_list:
            tl.reopen(item)
            print(" ", cr.render(item))


def cmd_edit(tl, args):
    """allows editing a given todo item
    """
    with ColorRenderer() as cr:
        if not args.item:
            open_editor(args.todo_file)
            quit(0)
        item = tl.get_item_by_index(args.item)
        print(cr.render(item))
        try:
            output = get_editor_input(item.text)
            # remove new lines
            item.text = output.replace("\r\n", " ").replace("\n", " ")
            tl.reparse_item(item)
            print(cr.render(item))
        except KeyboardInterrupt:
            # editing has been aborted
            pass


def cmd_delegated(tl, args):
    """shows all todo items that have been delegated and wait for input
    """
    with ColorRenderer() as cr:
        to_list = collections.defaultdict(list)
        for item in tl.list_items():
            if not args.all and item.done:
                continue
            for delegate in item.delegated_to:
                to_list[delegate.lower()].append(item)
        if args.delegate:
            del_list = [args.delegate.lower()]
        else:
            del_list = sorted(to_list.keys())
        for delegate in del_list:
            print("Delegated to", cr.wrap_delegate(delegate))
            for item in sorted(to_list[delegate], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_tasked(tl, args):
    """shows all open todo items that I am tasked with
    """
    with ColorRenderer() as cr:
        from_list = collections.defaultdict(list)
        for item in tl.list_items():
            if not args.all and item.done:
                continue
            for initiator in item.delegated_from:
                from_list[initiator.lower()].append(item)
        if args.initiator:
            ini_list = [args.initiator.lower()]
        else:
            ini_list = sorted(from_list.keys())

        for initiator in ini_list:
            print("Tasks from", cr.wrap_delegate(initiator))
            for item in sorted(from_list[initiator], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_overdue(tl, args):
    """shows all todo items that are overdue
    """
    with ColorRenderer() as cr:
        for item in [i for i in tl.list_items() if i.is_overdue()]:
            print(cr.render(item))


def cmd_report(tl, args):
    """shows a daily report of all done and report items
    """
    with ColorRenderer(args) as cr:
        # get list of done and report items
        report_list = [item for item in tl.list_items() if (item.done or item.is_report)]
        # default date used when no done date is specified
        na_date = datetime.datetime(1970, 1, 1)
        # sort filtered list by "done" date 
        report_list.sort(key=lambda x: x.properties.get("done", na_date), reverse=True)
        # group report/done items by date
        for keys, groups in groupby(report_list, 
            lambda x: (x.properties.get("done", na_date).year, 
                x.properties.get("done", na_date).month, 
                x.properties.get("done", na_date).day)):
            # filter out default dates again
            if (na_date.year, na_date.month, na_date.day) == keys:
                print("No done date attached")
            else:
                print("%d-%02d-%02d:" % keys)
            for item in groups:
                print(" ", cr.render(item))


def cmd_agenda(tl, args):
    """displays an agenda for a given date
    """
    with ColorRenderer(args) as cr:
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
                if is_same_day(args.date, comp_date):
                    agenda_items.append(item)
        agenda_items.sort(key=attrgetter("due_date"))
        print("Agenda for %d-%02d-%02d" % (args.date.year, args.date.month, args.date.day))
        for item in agenda_items:
            print(" ", cr.render(item))


def cmd_config(tl, args):
    """open todo.next configuration in editor
    """
    open_editor(args.config_file)


def cmd_stats(tl, args):
    """displays some simple statistics about your todo list
    """
    # write # open / # done / # prioritized / # overdue items
    counter = collections.defaultdict(int)
    delegates = set()
    with ColorRenderer() as cr:
        for item in tl.list_items():
            counter["total"] += 1
            if item.done:
                counter["done"] += 1
            else:
                counter["open"] += 1
            if item.priority:
                counter["prioritized"] += 1
            if item.is_overdue():
                counter["overdue"] += 1
            if item.is_report:
                counter["report"] += 1
            delegates.update(item.delegated_to)
            delegates.update(item.delegated_from)
        print("Total number of items: %d" % counter["total"])
        print(cr.wrap_done("Done items           : %d" % counter["done"]))
        print("Open items           : %d" % counter["open"])
        print(cr.wrap_prioritized("Prioritized items    : %d" % counter["prioritized"]))
        print(cr.wrap_overdue("Overdue items        : %d" % counter["overdue"]))
        print(cr.wrap_report("Report items         : %d" % counter["report"]))


def cmd_open(tl, args):
    """opens either an URL, a file or mail program depending on information that is attached to the todo item
    """
    with ColorRenderer(args) as cr:
        item = tl.get_item_by_index(args.item)
        nr = 0
        actions = {}
        for toopen in item.urls:
            print("  [% 2d] Open web site %s" % (nr, toopen))
            actions[nr] = (webbrowser.open_new_tab, toopen)
            nr += 1
        if item.properties.get("file", None):
            file_name = item.properties["file"]
            if not os.path.exists(file_name):
                print("  [xxx] File %s does not exist" % file_name)
            else:
                print("  [% 2d] Open file %s with default editor" % (nr, file_name))
                actions[nr] = (os.startfile, file_name)
                nr += 1
        if item.properties.get("mailto", None):
            email = item.properties["mailto"]
            print("  [% 2d] Write a mail to %s with default mail program" % (nr, email))
            actions[nr] = (os.startfile, "mailto:" + email)
        if len(actions) == 1:
            actions[0][0](actions[0][1])
        elif len(actions) > 1:
            choice = raw_input("Please enter your choice (0-%d): " % len(actions)-1).strip()
            try:
                choice = int(choice)
            except:
                print("Not a valid option. Closing...")
                quit(-1)
            if int(choice) in actions:
                actions[choice][0](actions[choice][1])
        else:
            print("No file / url / email found in task:")
            print(cr.render(item))


def cmd_project(tl, args):
    """lists all todo items per project
    """
    # lists todo items per project (like list, only with internal grouping)
    with ColorRenderer() as cr:
        project_dict = collections.defaultdict(list)
        for item in tl.list_items():
            if not args.all and item.done:
                continue
            for project in item.projects:
                project_dict[project].append(item)
        if args.name:
            args_list = [args.name,]
        else:
            args_list = sorted(project_dict.keys())
        
        for project in args_list:
            print("Project", cr.wrap_project(project))
            for item in sorted(project_dict[project], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_context(tl, args):
    """lists all todo items per context
    """
    # lists todo items per context (like list, only with internal grouping)
    with ColorRenderer() as cr:
        context_dict = collections.defaultdict(list)
        for item in tl.list_items():
            if not args.all and item.done:
                continue
            for context in item.contexts:
                context_dict[context].append(item)
        if args.name:
            args_list = [args.name,]
        else:
            args_list = sorted(context_dict.keys())
        
        for context in args_list:
            print("Context", cr.wrap_context(context))
            for item in sorted(context_dict[context], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_archive(tl, args):
    """archives all non-current todo items and removes them from todo list
    """
    # TODO: move all done / report items to another file and removes them from todo.txt
    raise NotImplementedError()


def cmd_delay(tl, args):
    """delays the due date of one or more todo items
    """
    # TODO: add relative date format like [+/-]12w4d5h20m
    raise NotImplementedError()


def cmd_clean(tl, args):
    """removes all outdated todo items from the todo list
    """
    # TODO: removes all outdated files from todo.txt - needs to be confirmed
    raise NotImplementedError()

def cmd_backup(tl, args):
    """backups the current todo file to a timestamped file
    """
    raise NotImplementedError()