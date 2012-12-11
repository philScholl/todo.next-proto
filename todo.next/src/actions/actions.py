"""
:mod:`actions.py`
~~~~~~~~~~~~~~~~~

Contains all actions that can be executed by ``todo.next``

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl <Phil@>
"""
from __future__ import print_function

from misc.cli_helpers import ColorRenderer, get_editor_input, open_editor, confirm_action, suppress_if_quiet
from misc.docdecorator import doc_description
from todo.date_trans import to_date, is_same_day, from_date
from todo.parsers import re_urls
from todo.config import ConfigBorg
from todo.todoitem import TodoItem
from todo.todolist import TodoList

import collections, datetime, re, os, glob
from itertools import groupby
import webbrowser, codecs
import logging

from operator import attrgetter

# configuration
conf = ConfigBorg()
# logger
logger = logging.getLogger("todonext.actions")

# regex for detecting priority argument in CLI
re_prio = re.compile("[xA-Z+-]", re.UNICODE)
# regex for replacing archive scheme variables with "*"
re_replace_archive_vars = re.compile("%\D", re.UNICODE)


@doc_description("lists all items that match the given expression", 
    "If no search query is given, all items are listed.", 
    {"search_string": "a search string",
    "all": "if given, also the done todo and report items are shown",
    "regex": "if given, the search string is interpreted as a regular expression",
    "ci": "if given, the search string is interpreted as case insensitive"})
def cmd_list(tl, args):
    """lists all items that match the given expression
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
        suppress_if_quiet(u"{nr_items} todo items displayed.".format(nr_items = nr), args)

@doc_description("adds a new todo item to the todo list", 
    "The source of the todo item can either be the command line or an editor.", 
    {"text": "the text of the todo item to add"})
def cmd_add(tl, args):
    """adds a new todo item to the todo list
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
        msg = u"Added {item}".format(item = cr.render(item))
        suppress_if_quiet(msg, args)
        logger.debug(msg)
        item.check()

@doc_description("removes one or more items from the todo list", None, 
    {"items": "the index numbers or IDs of the items to remove",
    "force": "if given, confirmation is not requested"})
def cmd_remove(tl, args):
    """removes one or more items from the todo list
    """
    with ColorRenderer() as cr:
        item_list = tl.get_items_by_index_list(args.items)
        if not item_list:
            msg = "Could not find item(s) {item_ids}".format(item_ids = ", ".join(args.items))
            print(msg)
            logger.info(msg)
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
        msg = u"{nr} todo items ({item_ids}) have been removed.".format(nr = len(item_list), item_ids = ",".join([cr.wrap_id(item.tid, reset=True) for item in item_list]))
        suppress_if_quiet(msg, args)
        logger.info(msg)

@doc_description("sets the status of one or more todo items to 'done'", None, 
    {"items": "the index numbers or IDs of the items to set to 'done'"})
def cmd_done(tl, args):
    """sets the status of one or more todo items to 'done'
    """
    with ColorRenderer() as cr:
        now = datetime.datetime.now()
        suppress_if_quiet(u"Marked following todo items as 'done':", args)
        for item in tl.get_items_by_index_list(args.items):
            tl.set_to_done(item)
            # if started property is set, remove it and update duration property
            if conf.STARTED in item.properties:
                start_time = item.properties[conf.STARTED]
                time_delta = now - start_time
                duration = 0
                try:
                    # try to parse existing duration property
                    duration = int(item.properties.get(conf.DURATION, 0))
                except:
                    pass
                # add delta time in minutes
                duration += int(time_delta.total_seconds() / 60) 
                # remove started property
                tl.replace_or_add_prop(item, conf.STARTED, None)
                # update duration property
                tl.replace_or_add_prop(item, conf.DURATION, duration)

            suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)

@doc_description("reopens one or more items marked as 'done'", None, 
    {"items": "the index numbers or IDs of the items to reopen"})
def cmd_reopen(tl, args):
    """reopens one or more items marked as 'done'
    """
    with ColorRenderer() as cr:
        suppress_if_quiet(u"Set the following todo items to open again:", args)
        for item in tl.get_items_by_index_list(args.items):
            tl.reopen(item)
            tl.reindex()
            suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)

@doc_description("allows editing a given todo item", 
    "This action will open an editor. "
        "If you're done editing, save the file and close the editor or cancel "
        "editing by pressing ``Ctrl+C``.", 
    {"item": "the index number or ID of the item to edit"})
def cmd_edit(tl, args):
    """allows editing a given todo item
    """
    with ColorRenderer() as cr:
        if not args.item:
            open_editor(conf.todo_file)
            quit(0)
        item = tl.get_item_by_index(args.item)
        if not item:
            print("Could not find item '{item_id}'".format(item_id = args.item))
            return
        
        print(" ", cr.render(item))
        try:
            output = get_editor_input(item.text)
            # remove new lines
            edited_item = TodoItem(output.replace("\r\n", " ").replace("\n", " ").strip())
            tl.replace_item(item, edited_item)
            suppress_if_quiet(u"  {item}".format(item = cr.render(edited_item)), args)
            edited_item.check()
        except KeyboardInterrupt:
            # editing has been aborted
            pass

@doc_description("shows all todo items that have been delegated and wait for input", 
    None, 
    {"delegate": "for filtering the name used for denoting a delegate",
    "all": "if given, also the done todos are shown"})
def cmd_delegated(tl, args):
    """shows all todo items that have been delegated and wait for input
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
            print("Delegated to {delegate}".format(delegate = cr.wrap_delegate(delegate, reset = True)))
            for item in sorted(to_list[delegate], cmp=tl.default_sort):
                nr += 1
                print(" ", cr.render(item))
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)

@doc_description("shows all open todo items that I am tasked with", None, 
    {"initiator": "for filtering the name used for denoting the initiator",
    "all": "if given, also the done todos are shown"})
def cmd_tasked(tl, args):
    """shows all open todo items that I am tasked with
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
            print("Tasks from {delegate}".format(delegate = cr.wrap_delegate(initiator, reset = True)))
            for item in sorted(from_list[initiator], cmp=tl.default_sort):
                print(" ", cr.render(item))
                nr += 1
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)

@doc_description("shows all todo items that are overdue")
def cmd_overdue(tl, args):
    """shows all todo items that are overdue
    """
    with ColorRenderer() as cr:
        print("Overdue todo items:")
        nr = 0
        for item in tl.list_items(lambda x: not x.done and x.is_overdue()):
            print(" ", cr.render(item))
            nr += 1
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)

@doc_description("shows a daily report of all done and report items", 
    "This command lists all done and report items for a given date "
        "or date range. If no arguments are given, the items of the last 7 days are "
        "displayed.", 
    {"from_date": "either a date or a string like 'tomorrow' or '*'",
    "to_date": "either a date or a string like 'tomorrow'"})
def cmd_report(tl, args):
    """shows a daily report of all done and report items
    """
    with ColorRenderer() as cr:
        # default date used when no done date is specified
        na_date = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)
        # today
        now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # check from and to date, make them datetime or None
        # what mode are we in?
        mode = None
        if args.from_date in ("*", "all"):
            mode, args.from_date, args.to_date = "ALL", na_date, now
        else:
            args.from_date = to_date(args.from_date)
            args.to_date = to_date(args.to_date)
            if isinstance(args.from_date, datetime.datetime):
                args.from_date = args.from_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                logger.debug(u"Cannot parse {date}".format(date = args.from_date))
                args.from_date = None
            if isinstance(args.to_date, datetime.datetime):
                args.to_date = args.to_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                logger.debug(u"Cannot parse {date}".format(date = args.to_date))
                args.to_date = None
        
        if args.from_date and args.to_date and not mode:
            mode = "RANGE"
        elif args.from_date and not args.to_date:
            mode, args.to_date = "DAY", args.from_date
        elif not mode:
            # last 7 days
            mode, args.from_date, args.to_date = "LASTWEEK", now - datetime.timedelta(days=7), now

        # swap dates, if necessary
        if args.from_date > args.to_date:
            args.from_date, args.to_date = args.to_date, args.from_date
        # set end date to end of day
        args.to_date = args.to_date.replace(hour=23, minute=59, second=59)
        
        logger.debug(u"Report mode {0}: from {1} to {2}".format(mode, args.from_date, args.to_date))
        
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
                    item.replace_or_add_prop(conf.ID, "(A)")
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
                print(u"Report for unknown date:")
            else:
                print(u"Report for {date}:".format(date = temp_date.strftime("%A, %Y-%m-%d")))
            # print the items, finally
            for item in groups:
                print(" ", cr.render(item))
                nr += 1
        
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)

@doc_description("displays an agenda for a given date",
    None, 
    {"date": "either a date or a string like 'tomorrow' or '*', default 'today'"})
def cmd_agenda(tl, args):
    """displays an agenda for a given date
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
                print(u"Could not parse date argument '{date_str}'".format(date_str = args.date))
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
                print(u"No done date attached")
            else:
                print(u"Agenda for {0:d}-{1:02d}-{2:02d}:".format(*keys))
            for item in groups:
                print(" ", cr.render(item))
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = len(agenda_items)), args)

@doc_description("open todo.next configuration in editor")
def cmd_config(tl, args): #@UnusedVariable
    """open todo.next configuration in editor
    """
    open_editor(conf.config_file)

@doc_description("assigns given items a priority (absolute like 'A' or relative like '-')", 
    None, 
    {"items": "the index numbers of the items to (re)prioritize",
    "priority": "the new priority ('A'..'Z' or '+'/'-') or 'x' (for removing)"})
def cmd_prio(tl, args):
    """assigns given items a priority (absolute like 'A' or relative like '-')
    """
    with ColorRenderer() as cr:
        prio_items = tl.get_items_by_index_list(args.items)
        if not prio_items:
            print(u"Could not find items {item_ids}".format(item_ids = ", ".join(args.items)))
            return
        new_prio = args.priority
        if not re_prio.match(new_prio):
            print(u"Priority '{prio}' can't be recognized (must be one of A to Z or +/-)".format(prio = new_prio))
            return
        for item in prio_items:
            old_prio = item.priority
            if new_prio == "x":
                # remove priority
                suppress_if_quiet(u"  Removing priority:", args)
                tl.set_priority(item, None)
                suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)
            elif new_prio == "-":
                if old_prio in ("Z", None):
                    print(u"  Can't lower priority of following item:")
                    print(u" ", cr.render(item))
                else:
                    temp_prio = chr(ord(old_prio)+1)
                    suppress_if_quiet(u"  Lower priority from {old_prio} to {new_prio}:".format(old_prio = old_prio, new_prio = temp_prio), args)
                    tl.set_priority(item, temp_prio)
                    suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)
            elif new_prio == "+":
                if old_prio in ("A", None):
                    print(u"  Can't raise priority of following item:")
                    print(u" ", cr.render(item))
                else:
                    temp_prio = chr(ord(old_prio)-1)
                    suppress_if_quiet(u"  Raise priority from {old_prio} to {new_prio}:".format(old_prio = old_prio, new_prio = temp_prio), args)
                    tl.set_priority(item, temp_prio)
                    suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)
            else:
                suppress_if_quiet(u"  Setting priority from {old_prio} to {new_prio}:".format(old_prio = old_prio, new_prio = new_prio), args)
                tl.set_priority(item, new_prio)
                suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)
                
@doc_description("displays some simple statistics about your todo list")
def cmd_stats(tl, args): #@UnusedVariable
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
            if item.is_overdue() and not item.done:
                counter["overdue"] += 1
            if item.is_still_open_today() and not item.done:
                counter["today"] += 1
            if item.is_report:
                counter["report"] += 1
            delegates.update(item.delegated_to)
            delegates.update(item.delegated_from)
        print(u"Total number of items: {stat}".format(stat = counter["total"]))
        print(u"Open items           : {stat}".format(stat = counter["open"]))
        print(cr.wrap_prioritized(u"Prioritized items    : {stat}".format(stat = counter["prioritized"])))
        print(cr.wrap_overdue(u"Overdue items        : {stat}".format(stat = counter["overdue"])))
        print(cr.wrap_today(u"Items due today      : {stat}".format(stat = counter["today"])))
        print(cr.wrap_done(u"Done items           : {stat}".format(stat = counter["done"])))
        print(cr.wrap_report(u"Report items         : {stat}".format(stat = counter["report"])))

@doc_description("opens either an URL, a file or mail program depending on information that is attached to the todo item",
    None, 
    {"item": "the index number of the item that has either an URL or file attached",})
def cmd_call(tl, args):
    """opens either an URL, a file or mail program depending on information that is attached to the todo item
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print(u"Could not find item '{item_id}'".format(item_id = args.item))
            return

        nr = 0
        actions = {}
        for toopen in item.urls:
            print(u"  [{nr: 3d}] Open web site {url}".format(nr = nr, url = toopen))
            actions[nr] = (webbrowser.open_new_tab, toopen)
            nr += 1
        for file_name in item.properties.get(conf.FILE, []):
            if not os.path.exists(file_name):
                print(u"  [xxx] File {fn} does not exist".format(fn = file_name))
            else:
                print(u"  [{nr: 3d}] Open file {fn} with default editor".format(nr = nr, fn = file_name))
                actions[nr] = (os.startfile, file_name)
                nr += 1
        for email in item.properties.get(conf.MAILTO, []):
            print(u"  [{nr: 3d}] Write a mail to {email} with default mail program".format(nr = nr, email = email))
            actions[nr] = (os.startfile, "mailto:" + email)
            nr += 1
        # simple case: only one action available
        if len(actions) == 1:
            actions[0][0](actions[0][1])
        elif len(actions) > 1:
            choice = raw_input(u"Please enter your choice (0-{max:d}): ".format(max = len(actions)-1)).strip()
            try:
                choice = int(choice)
            except:
                print(u"Not a valid option. Closing...")
                quit(-1)
            if int(choice) in actions:
                actions[choice][0](actions[choice][1])
        else:
            # nothing available
            print(u"No files / urls / email addresses found in task:")
            print(u" ", cr.render(item))

@doc_description("lists all todo items per project",
    None,
    {"name": "the name of the project to display",
     "all": "if given, also the done todo items are displayed",
     "ci": "if given, the project name is interpreted as case insensitive"})
def cmd_project(tl, args):
    """lists all todo items per project
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
            print(u"Project", cr.wrap_project(project, reset=True))
            for item in sorted(project_dict[project], cmp=tl.default_sort):
                nr += 1
                print(" ", cr.render(item))
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)
            
@doc_description("lists all todo items per context",
    None,
    {"name": "the name of the context to display",
     "all": "if given, also the done todo items are displayed",
     "ci": "if given, the context name is interpreted as case insensitive"})
def cmd_context(tl, args):
    """lists all todo items per context
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
            print(u"Context", cr.wrap_context(context, reset=True))
            for item in sorted(context_dict[context], cmp=tl.default_sort):
                print(u" ", cr.render(item))
                nr += 1 
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)

@doc_description("backups the current todo file to a timestamped file",
    None, 
    {"filename": "the name of the backup file [optional]",})
def cmd_backup(tl, args): #@UnusedVariable
    """backups the current todo file to a timestamped file
    """
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
        if not confirm_action(u"File {fn} already exists. Overwrite (y/N) ".format(fn = dst_fn)):
            print(u"  Aborting...")
            quit(0)
        else:
            print(u"  Overwriting {fn}...".format(fn = dst_fn))
    # copying the todo file to the destination
    with codecs.open(conf.todo_file, "r", "utf-8") as src:
        suppress_if_quiet(u"  Copying todo file to {fn}...".format(fn = dst_fn), args)
        with codecs.open(dst_fn, "w", "utf-8") as dst:
            dst.write(src.read())
    suppress_if_quiet(u"Successfully backed up todo file.", args)

@doc_description("archives all non-current todo items and removes them from todo list", 
    "This command moves all done / report items to other files (schema is specified in "
    "configuration) and removes them from the todo file.")
def cmd_archive(tl, args):
    """archives all non-current todo items and removes them from todo list
    """
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
    
    suppress_if_quiet(u"Successfully archived {nr} todo items.".format(nr = nr_archived), args)

@doc_description("delays the due date of one or more todo items",
    None,
    {"item": "the index number of the item to delay",
     "date": "either a date or a string like 'tomorrow', default '1d' (delays for 1 day)",
     "force": "if given, confirmation is not requested"})
def cmd_delay(tl, args):
    """delays the due date of one or more todo items
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print(u"Could not find item '{item_id}'".format(item_id = args.item))
            return
        if item.due_date:
            new_date = to_date(args.date, item.due_date)
            if isinstance(new_date, basestring):
                # remove first character, as it is "?" with a non-parsable date
                print(u"The given relative date could not be parsed: {date}".format(date = new_date[1:]))
            else:
                # ask for confirmation
                if not args.force:
                    print(" ", cr.render(item))
                    if not confirm_action(u"Delaying the preceding item's date from {from_date} to {to_date} (y/N)?".format(
                        from_date = from_date(item.due_date), to_date = from_date(new_date))):
                        return
                # do the actual replacement
                tl.replace_or_add_prop(item, conf.DUE, from_date(new_date), new_date)
        else:
            new_date = to_date(args.date)
            if not args.force:
                print(u" ", cr.render(item))
                if not confirm_action(u"The preceding item has no due date set, set to {date} (y/N)?".format(date = from_date(new_date))):
                    return
                tl.replace_or_add_prop(item, conf.DUE, from_date(new_date), new_date)
        suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)

@doc_description("lists all current and archived todo items that match the search string",
    None,
    {"search_string": "a search string",
     "regex": "if given, the search string is interpreted as a regular expression",
     "ci": "if given, the search string is interpreted as case insensitive"})
def cmd_search(tl, args):
    """lists all current and archived todo items that match the search string
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
                        item.replace_or_add_prop(conf.ID, "(A)")
                        all_matches.append((arch_file, item))
        
        # sort by filename
        all_matches.sort(key = lambda x:x[0])
        # group by filename
        for filename, items in groupby(all_matches, lambda x: x[0]):
            print(u"File '{fn}':".format(fn = filename))
            for item in items:
                print(" ", cr.render(item[1]))
        suppress_if_quiet(u"{nr} matching todo items found".format(nr = len(all_matches)), args)
        
@doc_description("attaches a file to the given todo item",
    None,
    {"item": "the index number of the item to which something should be attached",
     "location": "either a (relative) file name or a (fully qualified) URL"})
def cmd_attach(tl, args):
    """attaches a file to the given todo item
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print(u"Could not find item '{item_id}'".format(item_id = args.item))
            return

        if re_urls.match(args.location):
            # we got an URL
            suppress_if_quiet(u"Attaching URL {url}".format(url = args.location), args)
            item.text += u" {url}".format(url = args.location)
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
                print(u"File path '{fn}' does not exist".format(fn = path))
                quit(-1)
            
            suppress_if_quiet(u"Attaching file {fn}".format(fn = path), args)
            tl.replace_or_add_prop(item, conf.FILE, path)
            tl.reindex()
        suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)

@doc_description("detaches a file from a given todo item.",
    None,
    {"item": "the index number of the item from which something should be detached"})
def cmd_detach(tl, args):
    """detaches a file from a given todo item
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print(u"Could not find item '{item_id}'".format(item_id = args.item))
            return
        attmnt_list = []
        attmnt_list.extend(("url", url) for url in item.urls)
        for file_name in item.properties.get(conf.FILE, []):
            attmnt_list.append((conf.FILE, file_name))
        if len(attmnt_list) == 0:
            print(u"This item has no file or URLs attached")
            quit(0)
        elif len(attmnt_list) == 1:
            attmnt = attmnt_list[0]
        if len(attmnt_list) > 1:
            print(u"Please choose one of the following attachments to delete:")
            for nr, attmnt in enumerate(attmnt_list):
                print(u"  [{nr: 2d}] {attmnt}".format(nr = nr, attmnt = attmnt[1]))
            print(u"  [x] Abort operation")
            answer = raw_input(u"Your choice: ").lower().strip()
            if answer == "x":
                quit(0)
            try:
                attmnt_nr = int(answer)
                attmnt = attmnt_list[attmnt_nr]
            except:
                print(u"Not a valid input")
                quit(0)
        if attmnt[0] == conf.FILE:
            item = tl.replace_or_add_prop(item, conf.FILE, None, attmnt[1])
        else:
            item.text = u" ".join(item.text.replace(attmnt[1], "").split())
        suppress_if_quiet(u"  {item}".format(item = cr.render(item)), args)
        tl.dirty = True

@doc_description("checks the todo list for syntactical validity.")
def cmd_check(tl, args): #@UnusedVariable
    """checks the todo list for syntactical validity
    """
    with ColorRenderer() as cr:
        nr = 0
        for item, warnings in tl.check_items():
            nr += 1
            print(u" ", cr.render(item))
            for warning in warnings:
                print(u" ", warning)
        print(u"{nr} warning(s) have been found".format(nr = (nr or "No")))

@doc_description("marks the todo item as done and reenters it after the specified time",
    "This command is for frequently occurring todo items, like e.g. "
        "a bi-weekly status report.",
    {"item": "the index number of the item from which something should be detached",
    "date": "the relative or absolute date when the item is due again",})
def cmd_repeat(tl, args):
    """marks the todo item as done and reenters it after the specified time
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        # create a copy
        new_item = tl.add_item(item.text)
        # we have to create a new ID for the copied item
        new_item.remove_prop(conf.ID)
        tl.replace_or_add_prop(new_item, conf.ID, tl.create_tid(new_item))
        # set the due date of the new item to the specified date
        tl.replace_or_add_prop(new_item, conf.DUE, args.date, to_date(args.date))
        # set old item to done
        item.set_to_done()
        suppress_if_quiet(u"Marked todo item as 'done' and reinserted:\n  {item}".format(item = cr.render(new_item)), args)
        
@doc_description("lists all todo items (current and done) matching the given expression, equivalent to 'list --all'",
    "If no search query is given, all items are listed.",
    {"search_string": "a search string",
    "regex": "if given, the search string is interpreted as a regular expression",
    "ci": "if given, the search string is interpreted as case insensitive"})
def cmd_lsa(tl, args):
    """lists all todo items (current and done) matching the given expression, equivalent to "list --all"
    """
    args.all = True
    cmd_list(tl, args)

@doc_description("lists all items with markers (e.g. '(!)')",
    "Markers can be used to denote a todo item classification, e.g. "
        "an open question or an information ('(i)'). If no marker parameter "
        "is given, all found markers are listed.",
    {"marker": "a single character that denotes the type of the marker to list",
    "all": "if given, also the done todo and report items are shown"})
def cmd_mark(tl, args):
    """lists all items with markers (e.g. '(!)')
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
            print(cr.wrap_marker(u"({marker})".format(marker = marker), reset=True))
            for item in sorted(marker_dict[marker], cmp=tl.default_sort):
                print(u" ", cr.render(item))
                nr += 1
        suppress_if_quiet(u"{nr} todo items displayed.".format(nr = nr), args)
        

@doc_description("sets the 'started' property of an item or lists all started items.",
    "If a todo item is picked to be worked on, this command "
        "allows setting the started time. Thus, the time it took to work "
        "on that item can be derived from 'started' and 'done' time.",
    {"item": "the index number or id of the todo item which is started",})
def cmd_start(tl, args):
    """sets the 'started' property of an item or lists all started items.
    """
    with ColorRenderer() as cr:
        if not args.item:
            for item in tl.list_items(lambda x: True if conf.STARTED in x.properties 
                    and not (x.done or x.is_report) else False):
                print(u" ", cr.render(item))
        else:
            item = tl.get_item_by_index(args.item)
            if not item:
                print(u"No item found with number or ID '{item_id}'".format(item_id = args.item))
                return
            if item.done:
                print(u"Todo item has already been set to 'done':")
                print(u" ", cr.render(item))
                return
            if conf.STARTED in item.properties:
                print(u"Todo item has already been started on {date}".format(date = from_date(item.properties[conf.STARTED])))
                print(u" ", cr.render(item))
                return
            now = datetime.datetime.now()
            tl.replace_or_add_prop(item, conf.STARTED, from_date(now), now)
        

@doc_description("stops working on a todo item without setting it to 'done'",
    "If a todo item is paused, the 'duration' property is " 
        "updated and the 'started' property is removed.",
    {"item": "the index number or id of the todo item which should be stopped",})
def cmd_stop(tl, args):
    """stops working on a todo item without setting it to 'done'
    """
    with ColorRenderer() as cr:
        item = tl.get_item_by_index(args.item)
        if not item:
            print(u"No item found with number or ID '{item_id}'".format(item_id = args.item))
            return
        if conf.STARTED not in item.properties:
            print(u"Todo item has not been started yet")
            return
        start_time = item.properties[conf.STARTED]
        now = datetime.datetime.now()
        time_delta = now - start_time
        duration = 0
        try:
            # try to parse existing duration property
            duration = int(item.properties.get(conf.DURATION, 0))
        except:
            pass
        # add delta time in minutes
        duration += int(time_delta.total_seconds() / 60) 
        # remove started property
        tl.remove_prop(item, conf.STARTED, None)
        # update duration property
        tl.replace_or_add_prop(item, conf.DURATION, duration)
        suppress_if_quiet(u"You have worked {dur} minutes on:\n  {item}".format(dur = duration, item = cr.render(item)), args)
        

@doc_description("setting the first item as a pre-requisite to the second item",
    "This allows to create dependencies between todo items. One item "
        "can be set as a pre-requisite to another todo item. This command is only "
        "usable with id support activated.",
    {"item": "the id of the todo item which is a pre-requisite",
    "blocked": "the id of the todo item which should be blocked"})
def cmd_block(tl, args):
    """setting the first item as a pre-requisite to the second item
    """
    with ColorRenderer() as cr:
        if not conf.id_support:
            print(u"ID support is deactivated. You cannot use this feature.")
            return
        item = tl.get_item_by_index(args.item)
        blocked = tl.get_item_by_index(args.blocked)
        if item.tid in blocked.properties.get(conf.BLOCKEDBY, []):
            print(u"Todo item '{item_id}' is already a pre-requisite of '{blocked_id}'.".format(item_id = item, blocked_id = blocked))
            return
        tl.replace_or_add_prop(blocked, conf.BLOCKEDBY, item.tid)
        tl.clean_dependencies()
        tl.reindex()
        suppress_if_quiet(u"  {item}".format(item = cr.render(blocked)), args)
         

@doc_description("unsetting the first item as a pre-requisite to the second item",
    "This allows to remove dependencies between todo items. One item "
        "can be removed as a pre-requisite from another todo item. This command is only "
        "usable with id support activated.",
    {"item": "the id of the todo item which is a pre-requisite",
    "blocked": "the id of the todo item which is blocked"})
def cmd_unblock(tl, args):
    """unsetting the first item as a pre-requisite to the second item
    """
    with ColorRenderer() as cr:
        if not conf.id_support:
            print(u"ID support is deactivated. You cannot use this feature.")
            return
        item = tl.get_item_by_index(args.item)
        blocked = tl.get_item_by_index(args.blocked)
        if item.tid not in blocked.properties.get(conf.BLOCKEDBY, []):
            print(u"Todo item '{item_id}' is not a pre-requisite of '{blocked_id}'.".format(
                item_id = item, blocked_id = blocked))
            return
        tl.remove_prop(blocked, conf.BLOCKEDBY, item.tid)
        tl.clean_dependencies()
        tl.reindex()
        suppress_if_quiet(u"  {item}".format(item = cr.render(blocked)), args)


@doc_description("adding or editing a note to a todo item",
    "Opens a text file that contains further notes for a specific item.",
    {"item": "the id of the todo item that should be annotated",})
def cmd_note(tl, args):
    """adding or editing a note to a todo item
    """
    with ColorRenderer() as cr:
        if not conf.id_support:
            print(u"ID support is deactivated. You cannot use this feature.")
            return
        item = tl.get_item_by_index(args.item)
        # TODO: write me
    


@doc_description("lists items sorted by age (based on the 'created' property)",
    None,
    {"all": "if given, also done todo items are displayed",
    "desc": "if given, sorting is done descending with newest items first"})
def cmd_age(tl, args):
    """listing items sorted by age (based on ``created`` property)
    """
    with ColorRenderer() as cr:
        nr = 0
        itemlist = []
        for item in tl.list_items():
            if not item.get_created_date():
                # item does not have a creation date
                continue
            if (not args.all) and (item.is_report or item.done):
                # if --all is not set, report and done items are suppressed
                continue
            itemlist.append(item)
            nr += 1
        for item in sorted(itemlist, key=attrgetter("created_date"), reverse=args.desc):             
            print(" ", item.get_created_date().strftime("%Y-%m-%d %H:%M"), cr.render(item))
        suppress_if_quiet(u"{nr_items} todo items displayed.".format(nr_items = nr), args)
        print(cmd_age.__description, cmd_age.__params)
    

# Aliases
cmd_ls = cmd_list
cmd_ed = cmd_edit
cmd_rm = cmd_remove
cmd_due = cmd_delay
cmd_ctx = cmd_context
cmd_pr = cmd_project
cmd_rep = cmd_report
cmd_od = cmd_over = cmd_overdue
cmd_ag = cmd_agenda
cmd_x = cmd_done