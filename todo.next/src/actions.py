"""
:mod:`actions.py`
~~~~~~~~~~~~~~~~~

Contains all actions that can be executed by ``todo.next``

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl <Phil@>
"""
from __future__ import print_function
from cli_helpers import ColorRenderer, get_editor_input, open_editor
from date_trans import to_date, is_same_day, from_date

import collections, datetime, re, os
from operator import attrgetter
from itertools import groupby
import webbrowser, codecs
from todoitem import TodoItem

re_prio = re.compile("[xA-Z+-]")

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
                # if --all is not set, report and done items are suppressed
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
    with ColorRenderer(args) as cr:
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
    with ColorRenderer(args) as cr:
        item_list = tl.get_items_by_index_list(args.items)
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
                return
        else:
            for item in item_list:
                tl.remove_item(item)
        print("%d todo items have been removed." % len(item_list))

def cmd_done(tl, args):
    """sets the status of one or more todo items to 'done'
    """
    with ColorRenderer(args) as cr:
        print("Marked following todo items as 'done':")
        for item in tl.get_items_by_index_list(args.items):
            tl.set_to_done(item)
            print(" ", cr.render(item))


def cmd_reopen(tl, args):
    """reopens one or more items marked as 'done'
    """
    with ColorRenderer(args) as cr:
        print("Setting the following todo items to open again:")
        for item in tl.get_items_by_index_list(args.items):
            tl.reopen(item)
            print(" ", cr.render(item))


def cmd_edit(tl, args):
    """allows editing a given todo item
    """
    with ColorRenderer(args) as cr:
        if not args.item:
            open_editor(args.todo_file)
            quit(0)
        item = tl.get_item_by_index(args.item)
        print(cr.render(item))
        try:
            output = get_editor_input(item.text)
            # remove new lines
            edited_item = TodoItem(output.replace("\r\n", " ").replace("\n", " ").strip())
            tl.replace_item(item, edited_item)
            print(cr.render(edited_item))
        except KeyboardInterrupt:
            # editing has been aborted
            pass


def cmd_delegated(tl, args):
    """shows all todo items that have been delegated and wait for input
    """
    with ColorRenderer(args) as cr:
        to_list = collections.defaultdict(list)
        for item in tl.list_items():
            if not args.all and (item.done or item.is_report):
                continue
            for delegate in item.delegated_to:
                to_list[delegate.lower()].append(item)
        if args.delegate:
            del_list = [args.delegate.lower()]
        else:
            del_list = sorted(to_list)
        for delegate in del_list:
            print("Delegated to", cr.wrap_delegate(delegate))
            for item in sorted(to_list[delegate], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_tasked(tl, args):
    """shows all open todo items that I am tasked with
    """
    with ColorRenderer(args) as cr:
        from_list = collections.defaultdict(list)
        for item in tl.list_items():
            if not args.all and (item.done or item.is_report):
                continue
            for initiator in item.delegated_from:
                from_list[initiator.lower()].append(item)
        if args.initiator:
            ini_list = [args.initiator.lower()]
        else:
            ini_list = sorted(from_list)

        for initiator in ini_list:
            print("Tasks from", cr.wrap_delegate(initiator))
            for item in sorted(from_list[initiator], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_overdue(tl, args):
    """shows all todo items that are overdue
    """
    with ColorRenderer(args) as cr:
        print("Overdue todo items:")
        for item in tl.list_items(lambda x: not x.done and x.is_overdue()):
            print(" ", cr.render(item))


def cmd_report(tl, args):
    """shows a daily report of all done and report items
    """
    with ColorRenderer(args) as cr:
        # get list of done and report items
        report_list = list(tl.list_items(lambda x: x.done or x.is_report))
        # default date used when no done date is specified
        na_date = datetime.datetime(1970, 1, 1)
        # sort filtered list by "done" date 
        report_list.sort(key=lambda x: x.done_date or na_date, reverse=True)
        # group report/done items by date
        for keys, groups in groupby(report_list, 
            lambda x: ((x.done_date or na_date).year, (x.done_date or na_date).month, (x.done_date or na_date).day)
            ):
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
        for item in tl.list_items(lambda x: True if x.due_date else False):
            if is_same_day(args.date, item.due_date):
                agenda_items.append(item)
        agenda_items.sort(key=attrgetter("due_date"))
        print("Agenda for %d-%02d-%02d" % (args.date.year, args.date.month, args.date.day))
        for item in agenda_items:
            print(" ", cr.render(item))


def cmd_config(tl, args):
    """open todo.next configuration in editor
    """
    open_editor(args.config_file)


def cmd_prio(tl, args):
    """assigns given items a priority (absolute like 'A' or relative like '-')
    """
    with ColorRenderer(args) as cr:
        prio_items = tl.get_items_by_index_list(args.items)
        new_prio = args.priority
        if not re_prio.match(new_prio):
            print("Priority '%s' can't be recognized (must be one of A to Z or +/-)" % new_prio)
            return
        for item in prio_items:
            old_prio = item.priority
            if new_prio == "x":
                # remove priority
                print("  Removing priority:")
                tl.set_priority(item, None)
                print(" ", cr.render(item))
            elif new_prio == "-":
                if old_prio in ("Z", None):
                    print("  Can't lower priority of following item:")
                    print(" ", cr.render(item))
                else:
                    temp_prio = chr(ord(old_prio)+1)
                    print("  Lower priority from %s to %s:" % (old_prio, temp_prio))
                    tl.set_priority(item, temp_prio)
                    print(" ", cr.render(item))
            elif new_prio == "+":
                if old_prio in ("A", None):
                    print("  Can't raise priority of following item:")
                    print(" ", cr.render(item))
                else:
                    temp_prio = chr(ord(old_prio)-1)
                    print("  Raise priority from %s to %s:" % (old_prio, temp_prio))
                    tl.set_priority(item, temp_prio)
                    print(" ", cr.render(item))
            else:
                print("  Setting priority from %s to %s:" % (old_prio, new_prio))
                tl.set_priority(item, new_prio)
                print(" ", cr.render(item))
                
                
def cmd_stats(tl, args):
    """displays some simple statistics about your todo list
    """
    # write # open / # done / # prioritized / # overdue items
    counter = collections.defaultdict(int)
    delegates = set()
    with ColorRenderer(args) as cr:
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
    with ColorRenderer(args) as cr:
        project_dict = collections.defaultdict(list)
        for item in tl.list_items(lambda x: True if args.all or not (x.done or x.is_report) else False):
            for project in item.projects:
                project_dict[project].append(item)
        if args.name:
            #show project if the given name (partially) matches the project identifier
            args_list = [name for name in sorted(project_dict) if args.name in name]
        else:
            # show all sorted projects
            args_list = sorted(project_dict)
        for project in args_list:
            print("Project", cr.wrap_project(project))
            for item in sorted(project_dict[project], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_context(tl, args):
    """lists all todo items per context
    """
    # lists todo items per context (like list, only with internal grouping)
    with ColorRenderer(args) as cr:
        context_dict = collections.defaultdict(list)
        for item in tl.list_items(lambda x: True if args.all or not (x.done or x.is_report) else False):
            for context in item.contexts:
                context_dict[context].append(item)
        if args.name:
            #show context if the given name (partially) matches the context identifier
            args_list = [name for name in sorted(context_dict) if args.name in name]
        else:
            args_list = sorted(context_dict)
        
        for context in args_list:
            print("Context", cr.wrap_context(context))
            for item in sorted(context_dict[context], cmp=tl.default_sort):
                print(" ", cr.render(item))


def cmd_backup(tl, args):
    """backups the current todo file to a timestamped file
    """
    template = os.path.basename(args.todo_file)
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H%M_" + template)
    # backup directory can be relative to todo file directory
    backup_folder = os.path.join(os.path.dirname(args.todo_file), args.config.get("archive", "backup_dir"))
    # if not existing, create it
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    # a filename has been specified by command line arguments
    if args.filename:
        filename = args.filename
    # destination file
    dst_fn = os.path.join(backup_folder, filename)
    if os.path.exists(dst_fn):
        # file already exists: what to do?
        answer = raw_input("File %s already exists. Overwrite (y/N) " % dst_fn).lower().strip()
        if answer != "y":
            print("  Aborting...")
            quit(0)
        else:
            print("  Overwriting %s..." % dst_fn)
    # copying the todo file to the destination
    with codecs.open(args.todo_file, "r", "utf-8") as src:
        print("  Copying todo file to %s..." % dst_fn)
        with codecs.open(dst_fn, "w", "utf-8") as dst:
            dst.write(src.read())
    print("Successfully backed up todo file.")


def cmd_archive(tl, args):
    """archives all non-current todo items and removes them from todo list
    
    moves all done / report items to other files (schema is specified in
    configuration) and removes them from the todo file.
    """
    with ColorRenderer(args) as cr:
        # base directory of todo file
        base_dir = os.path.dirname(args.todo_file)
        
        # get list of done and report items
        report_list = list(tl.list_items(lambda x: x.done or x.is_report))
        # default date used when no done date is specified
        na_date = datetime.datetime(1970, 1, 1)
        # sort filtered list by "done" date 
        report_list.sort(key=lambda x: x.done_date or na_date, reverse=True)
        
        # for mapping items to file names
        file_map = collections.defaultdict(list)
        
        for item in report_list:
            item_date = item.done_date or na_date
            if is_same_day(item_date, na_date):
                dst_fn = args.config.get("archive", "archive_unsorted_filename")
            else:
                dst_fn = os.path.join(base_dir, item_date.strftime(args.config.get("archive", "archive_filename_scheme")))
            
            # if not existing, create it
            if not os.path.exists(os.path.dirname(dst_fn)):
                os.makedirs(os.path.dirname(dst_fn))
            # add to file map
            file_map[dst_fn].append(item)
        
        nr_archived = 0
        # now we append the items to the right file
        for dst_fn in file_map:
            nr_archived += len(file_map[dst_fn])
            # open files in append mode
            with codecs.open(dst_fn, "a", "utf-8") as fp:
                for item in file_map[dst_fn]:
                    # and write them
                    fp.write(item.text + "\n")
                    # and remove the item from todo list
                    tl.remove_item(item)
        
        print("Successfully archived %d todo items." % nr_archived)


def cmd_delay(tl, args):
    """delays the due date of one or more todo items
    """
    with ColorRenderer(args) as cr:
        item = tl.get_item_by_index(args.item)
        if item.due_date:
            new_date = to_date(args.date, item.due_date)
            if isinstance(new_date, basestring):
                # remove first character, as it is "?" with a non-parsable date
                print("The given relative date could not be parsed: %s" % new_date[1:])
            else:
                # ask for confirmation
                if not args.force:
                    print(" ", cr.render(item))
                    answer = raw_input("Delaying the preceding item's date from %s to %s (y/N)?" % 
                        (item.due_date, new_date)).strip().lower()
                    if answer != "y":
                        return
                # do the actual replacement
                tl.replace_or_add_prop(item, "due", from_date(new_date), new_date)
        else:
            new_date = to_date(args.date)
            if not args.force:
                print(" ", cr.render(item))
                answer = raw_input("The preceding item has no due date set, set to %s (y/N)?" % new_date).strip().lower()
                if answer != "y":
                    return
                tl.replace_or_add_prop(item, "due", from_date(new_date), new_date)
        print(" ", cr.render(item))


def cmd_clean(tl, args):
    """removes all outdated todo items from the todo list
    """
    # TODO: removes all outdated files from todo.txt - needs to be confirmed
    raise NotImplementedError()