"""
:mod:`actions.py`
~~~~~~~~~~~~~~~~~

Contains all actions that can be executed by ``todo.next``

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl <Phil@>
"""
from __future__ import print_function
from cli_helpers import ColorRenderer, get_editor_input, open_editor, confirm_action, suppress_if_quiet
from date_trans import to_date, is_same_day, from_date
from parsers import re_urls
from borg import ConfigBorg

import collections, datetime, re, os, glob
from itertools import groupby
import webbrowser, codecs
from todoitem import TodoItem
from todolist import TodoList

# regex for detecting priority argument in CLI
re_prio = re.compile("[xA-Z+-]", re.UNICODE)
# regex for replacing archive scheme variables with "*"
re_replace_archive_vars = re.compile("%\D", re.UNICODE)

def cmd_list(tl, args):
    """lists all items that match the given expression
    
    :description: If no search query is given, all items are listed.
    
    Required fields of :param:`args`:
    * search_string: a search string
    * all: if given, also the done todo and report items are shown
    * regex: if given, the search string is interpreted as a regular expression
    * ci: if given, the search string is interpreted as case insensitive
    """
    with ColorRenderer() as cr:
        # case insensitivity
        if args.ci:
            flags = re.UNICODE | re.IGNORECASE
        else:
            flags = re.UNICODE
        # no search string given
        if not args.search_string:
            args.search_string = "."
            args.regex = True
        # given as regular expression
        if args.regex:
            re_search = re.compile(args.search_string, flags)
        else:
            re_search = re.compile(re.escape(args.search_string), flags)
        
        nr = 0
        for item in tl.list_items():
            if (not args.all) and (item.is_report or item.done):
                # if --all is not set, report and done items are suppressed
                #print(repr(item.properties))
                continue
            if re_search.search(item.text):
                nr += 1 
                print(" ", cr.render(item))
        suppress_if_quiet("%d todo items displayed." % nr, args)
        

def cmd_add(tl, args):
    """adds a new todo item to the todo list
        
    :description: The source of the todo item can either be the command line or an editor.
    
    Required fields of :param:`args`:
    * text: the text of the todo item to add
    """
    with ColorRenderer() as cr:
        if not args.text:
            # no arguments given, open editor and let user enter data there
            output = get_editor_input("")
            item = tl.add_item(output.replace("\r\n", " ").replace("\n", " ").strip())
        elif isinstance(args.text, list):
            # string not enclosed in ""
            item = tl.add_item(" ".join(args.text))
        else:
            # single string 
            item = tl.add_item(args.text)
        suppress_if_quiet("Added %s" % cr.render(item), args)
        item.check()


def cmd_remove(tl, args):
    """removes one or more items from the todo list
    
    Required fields of :param:`args`:
    * items: the index number of the items to remove
    * force: if given, confirmation is not requested
    """
    with ColorRenderer() as cr:
        item_list = tl.get_items_by_index_list(args.items)
        if not item_list:
            print("Could not find item(s) %s" % ", ".join(args.items))
            return
        if not args.force:
            print("Do you really want to remove the following item(s):")
            for item in item_list:
                print(" ", cr.render(item))
            if confirm_action("Please confirm (y/N): "):
                for item in item_list:
                    tl.remove_item(item)
            else:
                print("Removing aborted")
                return
        else:
            for item in item_list:
                tl.remove_item(item)
        suppress_if_quiet("%d todo items have been removed." % len(item_list), args)


def cmd_done(tl, args):
    """sets the status of one or more todo items to 'done'
    
    Required fields of :param:`args`:
    * items: the index number of the items to set to 'done'
    """
    with ColorRenderer() as cr:
        suppress_if_quiet("Marked following todo items as 'done':", args)
        for item in tl.get_items_by_index_list(args.items):
            tl.set_to_done(item)
            suppress_if_quiet("  %s" % cr.render(item), args)


def cmd_reopen(tl, args):
    """reopens one or more items marked as 'done'
    
    Required fields of :param:`args`:
    * items: the index numbers of the items to reopen
    """
    with ColorRenderer() as cr:
        suppress_if_quiet("Set the following todo items to open again:", args)
        for item in tl.get_items_by_index_list(args.items):
            tl.reopen(item)
            tl.reindex()
            suppress_if_quiet("  %s" % cr.render(item), args)


def cmd_edit(tl, args):
    """allows editing a given todo item
    
    :description: This action will open an editor. 
        If you're done editing, save the file and close the editor or cancel
        editing by pressing ``Ctrl+C``.
    
    * item: the index number of the item to edit
    """
    with ColorRenderer() as cr:
        conf = ConfigBorg()
        if not args.item:
            open_editor(conf.todo_file)
            quit(0)
        item = tl.get_item_by_index(args.item)
        if not item:
            print("Could not find item '%s'" % args.item)
            return
        
        print(" ", cr.render(item))
        try:
            output = get_editor_input(item.text)
            # remove new lines
            edited_item = TodoItem(output.replace("\r\n", " ").replace("\n", " ").strip())
            tl.replace_item(item, edited_item)
            suppress_if_quiet("  %s" % cr.render(edited_item), args)
            edited_item.check()
        except KeyboardInterrupt:
            # editing has been aborted
            pass


def cmd_delegated(tl, args):
    """shows all todo items that have been delegated and wait for input
    
    Required fields of :param:`args`:
    * delegate: for filtering the name used for denoting a delegate
    * all: if given, also the done todos are shown
    """
    with ColorRenderer() as cr:
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
        nr = 0
        for delegate in del_list:
            print("Delegated to", cr.wrap_delegate(delegate))
            for item in sorted(to_list[delegate], cmp=tl.default_sort):
                nr += 1
                print(" ", cr.render(item))
        suppress_if_quiet("%d todo items displayed." % nr, args)


def cmd_tasked(tl, args):
    """shows all open todo items that I am tasked with
    
    Required fields of :param:`args`:
    * initiator: for filtering the name used for denoting the initiator
    * all: if given, also the done todos are shown
    """
    with ColorRenderer() as cr:
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
        nr = 0
        for initiator in ini_list:
            print("Tasks from", cr.wrap_delegate(initiator))
            for item in sorted(from_list[initiator], cmp=tl.default_sort):
                print(" ", cr.render(item))
                nr += 1
        suppress_if_quiet("%d todo items displayed." % nr, args)
            

def cmd_overdue(tl, args):
    """shows all todo items that are overdue
    
    Nor :param:`args` arguments are required.
    """
    with ColorRenderer() as cr:
        print("Overdue todo items:")
        nr = 0
        for item in tl.list_items(lambda x: not x.done and x.is_overdue()):
            print(" ", cr.render(item))
            nr += 1
        suppress_if_quiet("%d todo items displayed." % nr, args)


def cmd_report(tl, args):
    """shows a daily report of all done and report items
    
    :description: This command lists all done and report items for a given date
        or date range. If no arguments are given, all available todo items are
        displayed. 
    
    Required fields of :param:`args`:
    * from_date: either a date or a string like 'tomorrow' or '*'
    * to_date: either a date or a string like 'tomorrow' or '*'
    """
    with ColorRenderer() as cr:
        # get configuration
        conf = ConfigBorg()
        # default date used when no done date is specified
        na_date = datetime.datetime(1970, 1, 1)
        # check from and to date, make them datetime or None
        for nr, tdate in enumerate([args.from_date, args.to_date]):
            pdate = to_date(tdate)
            if isinstance(pdate, basestring):
                pdate = None
            if nr == 0:
                args.from_date = pdate
            elif nr == 1:
                args.to_date = pdate
        
        # what mode are we in?
        mode = None
        if args.from_date and args.to_date:
            mode = "RANGE"
        elif args.from_date and not args.to_date:
            mode, args.to_date = "DAY", args.from_date
        else:
            mode, args.from_date, args.to_date = "ALL", na_date, datetime.datetime.now()

        # swap dates, if necessary
        if args.from_date > args.to_date:
            args.from_date, args.to_date = args.to_date, args.from_date
        # set end date to end of day
        args.to_date = args.to_date.replace(hour=23, minute=59, second=59)
        
        #TODO: for logging print(mode, args.from_date, args.to_date)
        
        # get list of done and report items from current todo list
        report_list = list(tl.list_items(lambda x: (x.done or x.is_report)))
        
        # get list of done and report items from un-dated archive file
        root_dir = os.path.dirname(conf.todo_file)
        unsorted_fn = os.path.join(root_dir, conf.archive_unsorted_filename)
        if os.path.exists(unsorted_fn):
            res = TodoList(unsorted_fn)
            report_list.extend(res.todolist)
        
        # get all archive file names in list
        file_pattern = re_replace_archive_vars.sub("*", conf.archive_filename_scheme)
        file_list = glob.glob(os.path.join(root_dir, file_pattern))

        # regex for finding all replaced parts in archive filename scheme
        re_find_date_str = re_replace_archive_vars.sub("(.+)", conf.archive_filename_scheme).replace("\\", "\\\\")
        re_find_date = re.compile(re_find_date_str, re.UNICODE)
        # loop through all files and see, whether they match the given date range
        for fn in file_list:
            # get all replaced values in filename
            parts = re_find_date.findall(fn)[0]
            # get the variables responsible for this substitution (e.archived_items. "%Y", "%m", ...)
            tvars = re_replace_archive_vars.findall(conf.archive_filename_scheme)
            # create mapping, removing duplicates
            mapping = dict(zip(tvars, parts))
            # create date from mapping
            tdate = datetime.datetime.strptime(" ".join(mapping.values()), " ".join(mapping))
            
            # if filename matches date range
            if args.from_date <= tdate <= args.to_date:
                # load todo list
                res = TodoList(fn)
                # get items directly if they are done or report items
                archived_items = [item for item in res.todolist if item.done or item.is_report]
                for item in archived_items:
                    # replace id with (A) to mark it as archived
                    item.tid = "(A)"
                # append it to candidates
                report_list.extend(archived_items)
        
        # sort filtered list by "done" date 
        report_list.sort(key=lambda x: x.done_date or na_date)
        
        nr = 0
        # group report/done items by date
        for keys, groups in groupby(report_list, 
            lambda x: ((x.done_date or na_date).year, (x.done_date or na_date).month, (x.done_date or na_date).day)
            ):
            # we are looking at that date right now
            temp_date = datetime.datetime(year=keys[0], month=keys[1], day=keys[2])
            # that date does not match the requested date range: skip
            if not args.from_date <= temp_date <= args.to_date:
                continue
            # filter out default dates again
            if is_same_day(na_date, temp_date):
                print("Report for unknown date:")
            else:
                print("Report for %s:" % temp_date.strftime("%A, %Y-%m-%d"))
            # print the items, finally
            for item in groups:
                print(" ", cr.render(item))
                nr += 1
        
        suppress_if_quiet("%d todo items displayed." % nr, args)


def cmd_agenda(tl, args):
    """displays an agenda for a given date
    
    Required fields of :param:`args`:
    * date: either a date or a string like 'tomorrow' or '*', default 'today'
    """
    with ColorRenderer() as cr:
        agenda_items = []
        # if not set, get agenda for today
        list_all = False
        if not args.date:
            args.date = datetime.datetime.now()
        elif args.date == "*":
            list_all = True
        else:
            args.date = to_date(args.date)
            if isinstance(args.date, basestring):
                print("Could not parse date argument '%s'" % args.date)
                quit(-1)
        for item in tl.list_items(lambda x: True if x.due_date else False):
            if is_same_day(args.date, item.due_date) or list_all:
                agenda_items.append(item)
        # default date used when no done date is specified
        na_date = datetime.datetime(1970, 1, 1)
        # sort filtered list by "due" date and whether they are already marked as "done" 
        agenda_items.sort(key=lambda x: (x.done, x.due_date) or (x.done, na_date))
        # group report/done items by date
        for keys, groups in groupby(agenda_items, 
            lambda x: ((x.due_date or na_date).year, (x.due_date or na_date).month, (x.due_date or na_date).day)
            ):
            # filter out default dates again
            if (na_date.year, na_date.month, na_date.day) == keys:
                print("No done date attached")
            else:
                print("Agenda for %d-%02d-%02d:" % keys)
            for item in groups:
                print(" ", cr.render(item))
        suppress_if_quiet("%d todo items displayed." % len(agenda_items), args)


def cmd_config(tl, args):
    """open todo.next configuration in editor
    
    Required fields of :param:`args`:
    """
    conf = ConfigBorg()
    open_editor(conf.config_file)


def cmd_prio(tl, args):
    """assigns given items a priority (absolute like 'A' or relative like '-')
    
    Required fields of :param:`args`:
    * items: the index numbers of the items to (re)prioritize
    * priority: the new priority ('A'..'Z' or '+'/'-') or 'x' (for removing)
    """
    with ColorRenderer() as cr:
        prio_items = tl.get_items_by_index_list(args.items)
        if not prio_items:
            print("Could not find items %s" % ", ".join(args.items))
            return
        new_prio = args.priority
        if not re_prio.match(new_prio):
            print("Priority '%s' can't be recognized (must be one of A to Z or +/-)" % new_prio)
            return
        for item in prio_items:
            old_prio = item.priority
            if new_prio == "x":
                # remove priority
                suppress_if_quiet("  Removing priority:", args)
                tl.set_priority(item, None)
                suppress_if_quiet("  %s" % cr.render(item), args)
            elif new_prio == "-":
                if old_prio in ("Z", None):
                    print("  Can't lower priority of following item:")
                    print(" ", cr.render(item))
                else:
                    temp_prio = chr(ord(old_prio)+1)
                    suppress_if_quiet("  Lower priority from %s to %s:" % (old_prio, temp_prio), args)
                    tl.set_priority(item, temp_prio)
                    suppress_if_quiet("  %s" % cr.render(item), args)
            elif new_prio == "+":
                if old_prio in ("A", None):
                    print("  Can't raise priority of following item:")
                    print(" ", cr.render(item))
                else:
                    temp_prio = chr(ord(old_prio)-1)
                    suppress_if_quiet("  Raise priority from %s to %s:" % (old_prio, temp_prio), args)
                    tl.set_priority(item, temp_prio)
                    suppress_if_quiet("  %s" % cr.render(item), args)
            else:
                suppress_if_quiet("  Setting priority from %s to %s:" % (old_prio, new_prio), args)
                tl.set_priority(item, new_prio)
                suppress_if_quiet("  %s" % cr.render(item), args)
                
                
def cmd_stats(tl, args):
    """displays some simple statistics about your todo list
    
    Required fields of :param:`args`:
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
            if item.is_overdue() and not item.done:
                counter["overdue"] += 1
            if item.is_still_open_today() and not item.done:
                counter["today"] += 1
            if item.is_report:
                counter["report"] += 1
            delegates.update(item.delegated_to)
            delegates.update(item.delegated_from)
        print("Total number of items: %d" % counter["total"])
        print("Open items           : %d" % counter["open"])
        print(cr.wrap_prioritized("Prioritized items    : %d" % counter["prioritized"]))
        print(cr.wrap_overdue("Overdue items        : %d" % counter["overdue"]))
        print(cr.wrap_today("Items due today      : %d" % counter["today"]))
        print(cr.wrap_done("Done items           : %d" % counter["done"]))
        print(cr.wrap_report("Report items         : %d" % counter["report"]))


def cmd_call(tl, args):
    """opens either an URL, a file or mail program depending on information that is attached to the todo item
    
    Required fields of :param:`args`:
    * item: the index number of the item that has either an URL or file attached
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print("Could not find item '%s'" % args.item)
            return

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
            print(" ", cr.render(item))


def cmd_project(tl, args):
    """lists all todo items per project
    
    Required fields of :param:`args`:
    * name: the name of the project to display
    * all: if given, also the done todo items are displayed
    * ci: if given, the project name is interpreted as case insensitive
    """
    # lists todo items per project (like list, only with internal grouping)
    with ColorRenderer() as cr:
        # case insensitivity
        if args.ci:
            flags = re.UNICODE | re.IGNORECASE
        else:
            flags = re.UNICODE
        if args.name:
            args.name = re.escape(args.name)
        else:
            args.name = "."
        re_search = re.compile(args.name, flags)
        
        project_dict = collections.defaultdict(list)
        for item in tl.list_items(lambda x: True if args.all or not (x.done or x.is_report) else False):
            for project in item.projects:
                project_dict[project].append(item)
        #show project if the given name (partially) matches the project identifier
        args_list = [name for name in sorted(project_dict) if re_search.search(name)]
        nr = 0
        for project in args_list:
            print("Project", cr.wrap_project(project, reset=True))
            for item in sorted(project_dict[project], cmp=tl.default_sort):
                nr += 1
                print(" ", cr.render(item))
        suppress_if_quiet("%d todo items displayed." % nr, args)
            

def cmd_context(tl, args):
    """lists all todo items per context
    
    Required fields of :param:`args`:
    * name: the name of the context to display
    * all: if given, also the done todo items are displayed
    * ci: if given, the context name is interpreted as case insensitive
    """
    # lists todo items per context (like list, only with internal grouping)
    with ColorRenderer() as cr:
        # case insensitivity
        if args.ci:
            flags = re.UNICODE | re.IGNORECASE
        else:
            flags = re.UNICODE
        if args.name:
            args.name = re.escape(args.name)
        else:
            args.name = "."
        re_search = re.compile(args.name, flags)

        context_dict = collections.defaultdict(list)
        for item in tl.list_items(lambda x: True if args.all or not (x.done or x.is_report) else False):
            for context in item.contexts:
                context_dict[context].append(item)
        #show context if the given name (partially) matches the context identifier
        args_list = [name for name in sorted(context_dict) if re_search.search(name)]
        nr = 0
        for context in args_list:
            print("Context", cr.wrap_context(context, reset=True))
            for item in sorted(context_dict[context], cmp=tl.default_sort):
                print(" ", cr.render(item))
                nr += 1 
        suppress_if_quiet("%d todo items displayed." % nr, args)


def cmd_backup(tl, args):
    """backups the current todo file to a timestamped file
    
    Required fields of :param:`args`:
    """
    conf = ConfigBorg()
    template = os.path.basename(conf.todo_file)
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H%M_" + template)
    # backup directory can be relative to todo file directory
    backup_folder = os.path.join(os.path.dirname(conf.todo_file), conf.backup_dir)
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
        if not confirm_action("File %s already exists. Overwrite (y/N) " % dst_fn):
            print("  Aborting...")
            quit(0)
        else:
            print("  Overwriting %s..." % dst_fn)
    # copying the todo file to the destination
    with codecs.open(conf.todo_file, "r", "utf-8") as src:
        suppress_if_quiet("  Copying todo file to %s..." % dst_fn, args)
        with codecs.open(dst_fn, "w", "utf-8") as dst:
            dst.write(src.read())
    suppress_if_quiet("Successfully backed up todo file.", args)


def cmd_archive(tl, args):
    """archives all non-current todo items and removes them from todo list
    
    moves all done / report items to other files (schema is specified in
    configuration) and removes them from the todo file.
    
    Required fields of :param:`args`:
    """
    with ColorRenderer() as cr:
        conf = ConfigBorg()
        # base directory of todo file
        base_dir = os.path.dirname(conf.todo_file)
        
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
                dst_fn = conf.archive_unsorted_filename
            else:
                dst_fn = os.path.join(base_dir, item_date.strftime(conf.archive_filename_scheme))
            
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
        
        suppress_if_quiet("Successfully archived %d todo items." % nr_archived, args)


def cmd_delay(tl, args):
    """delays the due date of one or more todo items
    
    Required fields of :param:`args`:
    * item: the index number of the item to delay
    * date: either a date or a string like 'tomorrow', default '1d' (delays for 1 day)
    * force: if given, confirmation is not requested
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print("Could not find item '%s'" % args.item)
            return
        if item.due_date:
            new_date = to_date(args.date, item.due_date)
            if isinstance(new_date, basestring):
                # remove first character, as it is "?" with a non-parsable date
                print("The given relative date could not be parsed: %s" % new_date[1:])
            else:
                # ask for confirmation
                if not args.force:
                    print(" ", cr.render(item))
                    if not confirm_action("Delaying the preceding item's date from %s to %s (y/N)?" % 
                        (from_date(item.due_date), from_date(new_date))):
                        return
                # do the actual replacement
                tl.replace_or_add_prop(item, "due", from_date(new_date), new_date)
        else:
            new_date = to_date(args.date)
            if not args.force:
                print(" ", cr.render(item))
                if not confirm_action("The preceding item has no due date set, set to %s (y/N)?" % from_date(new_date)):
                    return
                tl.replace_or_add_prop(item, "due", from_date(new_date), new_date)
        suppress_if_quiet("  %s" % cr.render(item), args)


def cmd_clean(tl, args):
    """removes all outdated todo items from the todo list
    
    Required fields of :param:`args`:
    """
    # TODO: removes all outdated files from todo.txt - needs to be confirmed
    raise NotImplementedError()


def cmd_search(tl, args):
    """lists all current and archived todo items that match the search string
    
    Required fields of :param:`args`:
    * search_string: a search string
    * regex: if given, the search string is interpreted as a regular expression
    * ci: if given, the search string is interpreted as case insensitive
    """
    with ColorRenderer() as cr:
        conf = ConfigBorg()
        
        # case insensitivity
        if args.ci:
            flags = re.UNICODE | re.IGNORECASE
        else:
            flags = re.UNICODE
        # no search string given
        if not args.search_string:
            args.search_string = "."
            args.regex = True
        # given as regular expression
        if args.regex:
            re_search = re.compile(args.search_string, flags)
        else:
            re_search = re.compile(re.escape(args.search_string), flags)

        # store for all matching items
        all_matches = []
        # first, look at current todo list
        for item in tl.list_items():
            if re_search.search(item.text):
                all_matches.append((conf.todo_file, item))
        
        # get file list of all archive files by replacing all %x-variables with '*' and
        # let glob do the hard work
        file_pattern = re_replace_archive_vars.sub("*", conf.archive_filename_scheme)
        root_dir = os.path.dirname(conf.todo_file)
        file_list = glob.glob(os.path.join(root_dir, file_pattern))
        # add the file for items without done timestamp
        unsorted_file = os.path.join(root_dir, conf.archive_unsorted_filename)
        if os.path.exists(unsorted_file):
            file_list.append(unsorted_file)
        
        for arch_file in file_list:
            # create a new todo list for each archive file
            with TodoList(arch_file) as atl:
                for item in atl.todolist:
                    if re_search.search(item.text):
                        all_matches.append((arch_file, item))
        
        # sort by filename
        all_matches.sort(key = lambda x:x[0])
        # group by filename
        for filename, items in groupby(all_matches, lambda x: x[0]):
            print("File '%s':" % filename)
            for item in items:
                print(" ", cr.render(item[1]))
        suppress_if_quiet("%d matching todo items found" % len(all_matches), args)
        
        
def cmd_attach(tl, args):
    """attaches a file to the given todo item
    
    Required fields of :param:`args`:
    * item: the index number of the item to which something should be attached
    * location: either a (relative) file name or a (fully qualified) URL
    """
    with ColorRenderer() as cr:
        conf = ConfigBorg()
        item = tl.get_item_by_index(args.item)
        if not item:
            print("Could not find item '%s'" % args.item)
            return

        if re_urls.match(args.location):
            # we got an URL
            suppress_if_quiet("Attaching URL %s" % args.location, args)
            item.text += " %s" % args.location
            item.urls.append(args.location.strip())
            tl.dirty = True
            tl.reindex() 
        else:
            # get path relative to todo file
            try:
                path = os.path.relpath(args.location, os.path.dirname(conf.todo_file))
            except ValueError:
                # path is on other rive than reference location
                path = os.path.abspath(args.location)
                
            if not os.path.exists(path):
                print("File path '%s' does not exist" % path)
                quit(-1)

            if item.properties.get("file", None):
                print("A file is already attached to this item: %s" % item.properties["file"])
                if not confirm_action("Do you want to replace this file reference with the file '%s' (y/N)" % path):
                    quit(0)
            suppress_if_quiet("Attaching file %s" % path, args)
            tl.replace_or_add_prop(item, "file", path)
            tl.reindex()
        suppress_if_quiet("  %s" % cr.render(item), args)


def cmd_detach(tl, args):
    """detaches a file from a given todo item
    
    Required fields of :param:`args`:
    * item: the index number of the item from which something should be detached
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print("Could not find item '%s'" % args.item)
            return
        attmnt_list = []
        attmnt_list.extend(("url", url) for url in item.urls)
        if item.properties.get("file", None):
            attmnt_list.append(("file", item.properties["file"]))
        if len(attmnt_list) == 0:
            print("This item has no file or URLs attached")
            quit(0)
        elif len(attmnt_list) == 1:
            attmnt = attmnt_list[0]
        if len(attmnt_list) > 1:
            print("Please choose one of the following attachments to delete:")
            for nr, attmnt in enumerate(attmnt_list):
                print("  [%d] %s" % (nr, attmnt[1]))
            print("  [x] Abort operation")
            answer = raw_input("Your choice: ").lower().strip()
            if answer == "x":
                quit(0)
            try:
                attmnt_nr = int(answer)
                attmnt = attmnt_list[attmnt_nr]
            except:
                print("Not a valid input")
                quit(0)
        if attmnt[0] == "file":
            item = tl.replace_or_add_prop(item, "file", None)
        else:
            item.text = " ".join(item.text.replace(attmnt[1], "").split())
        suppress_if_quiet("  %s" % cr.render(item), args)
        tl.dirty = True


def cmd_check(tl, args):
    """checks the todo list for syntactical validity
    
    Required fields of :param:`args`:
    """
    with ColorRenderer() as cr:
        nr = 0
        for item, warnings in tl.check_items():
            nr += 1
            print(" ", cr.render(item))
            for warning in warnings:
                print(" ", warning)
        print("%s warning(s) have been found" % (nr or "No"))


def cmd_repeat(tl, args):
    """marks the todo item as done and reenters it after the specified time
    
    :description: This command is for frequently occurring todo items, like e.g. a bi-weekly
                  status report.
    
    Required fields of :param:`args`:
    * item: the index number of the item from which something should be detached
    * date: the relative or absolute date when the item is due again 
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        new_item = tl.add_item(item.text)
        item.set_to_done()
        tl.replace_or_add_prop(new_item, "due", args.date, to_date(args.date))
        suppress_if_quiet("Marked todo item as 'done' and reinserted:\n  %s" % cr.render(new_item), args)
        

def cmd_lsa(tl, args):
    """lists all todo items (current and done) matching the given expression, equivalent to "list --all"
    
    :description: If no search query is given, all items are listed.
    
    Required fields of :param:`args`:
    * search_string: a search string
    * regex: if given, the search string is interpreted as a regular expression
    * ci: if given, the search string is interpreted as case insensitive
    """
    args.all = True
    cmd_list(tl, args)


def cmd_mark(tl, args):
    """lists all items with markers (e.g. '(!)')
    
    :description: Markers can be used to denote a todo item classification, e.g.
        an open question or an information ('(i)'). If no marker parameter
        is given, all found markers are listed.
    
    Required fields of :param:`args`:
    * marker: a single character that denotes the type of the marker to list.
    * all: if given, also the done todo and report items are shown
    """
    with ColorRenderer() as cr:
        marker_dict = collections.defaultdict(list)
        for item in tl.list_items(lambda x: True if args.all or not (x.done or x.is_report) else False):
            for marker in item.markers:
                marker_dict[marker].append(item)
        if args.marker:
            #show project if the given name (partially) matches the project identifier
            args_list = [name for name in sorted(marker_dict) if args.marker == name]
        else:
            # show all sorted projects
            args_list = sorted(marker_dict)
            
        nr = 0
        for marker in args_list:
            print(cr.wrap_marker("(%s)" % marker, reset=True))
            for item in sorted(marker_dict[marker], cmp=tl.default_sort):
                print(" ", cr.render(item))
                nr += 1
        suppress_if_quiet("%d todo items displayed." % nr, args)
        
        
# Aliases
cmd_ls = cmd_list
cmd_ed = cmd_edit
cmd_rm = cmd_del = cmd_remove
cmd_ctx = cmd_context
cmd_pr = cmd_project
cmd_rep = cmd_report
cmd_od = cmd_over = cmd_overdue
cmd_ag = cmd_agenda
cmd_x = cmd_done