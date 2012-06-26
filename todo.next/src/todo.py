"""

.. see:: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
from date_trans import to_date
from col_renderer import ColorRenderer
from todolist import TodoList
from operator import attrgetter
import datetime
import argparse
import tempfile, os, subprocess
import codecs
import time


    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Todo.txt file CLI interface", 
        epilog="For more, see https://github.com/philScholl/todo.next-proto",
        #argument_default=argparse.SUPPRESS
        )
    parser.add_argument("-v", action="count")
    
    subparser = parser.add_subparsers(title="subcommands", help = "sub command help", dest = "action")
    
    parse_add = subparser.add_parser("add", help="adds a new item to the todo list")
    parse_add.add_argument("text", type=str, help="the item to add")
    
    parse_del = subparser.add_parser("remove", help="removes an item from the todo list")
    parse_del.add_argument("item", type=int, help="the index number of the item to remove")
    parse_del.add_argument("--force", action="store_true")
    
    parse_list = subparser.add_parser("list", help="lists all items that match the given expression") #, aliases=["ls"]
    parse_list.add_argument("search_string", type=str, help="a search string", nargs="?")
    
    parse_agenda = subparser.add_parser("agenda", help="prints the agenda for a given date")
    parse_agenda.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default 'today'", nargs="?")
    
    parse_done = subparser.add_parser("done", help="sets a todo item to 'done' status")
    parse_done.add_argument("item", type=int, help="the index number of the item to set to 'done'")
    
    parse_reopen = subparser.add_parser("reopen", help="reopens a todo item already done")
    parse_reopen.add_argument("item", type=int, help="the index number of the item to reopen")
    
    parse_edit = subparser.add_parser("edit", help="allows editing a todo item", description="This action will open an editor. If you're done editing, save the file and close the editor.")
    parse_edit.add_argument("item", type=int, help="the index number of the item to edit", nargs="?")
    
    parse_delay = subparser.add_parser("delay", help="delays todo item's due date")
    parse_delay.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default '1d' (delays for 1 day)", nargs="?")
    
    parse_delegated = subparser.add_parser("delegated", help="shows all delegated items that are still open")
    parse_agenda.add_argument("delegate", type=str, help="for filtering the name used for denoting a delegate", nargs="?")
    
    parse_mytasks = subparser.add_parser("tasks", help="shows all items that have been assigned to you")
    parse_agenda.add_argument("search_string", type=str, help="a search string", nargs="?")
    
    parse_overdue = subparser.add_parser("overdue", help="shows all items that are overdue")
    
    parse_archive = subparser.add_parser("archive", help="archives all non-current todo items and removes them from todo.txt")
    parse_archive.add_argument("to_file", type=str, help="the file where all archived todo items are appended")
    
    parse_report = subparser.add_parser("report", help="shows a report of all done and report items")
    parse_report.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default 'today'", nargs="?")
    
    parse_clean = subparser.add_parser("clean", help="removes all outdated todo items from the todo.txt")
    
    parse_open = subparser.add_parser("open", help="opens either an URL or a file that is attached to the todo item")
    parse_open.add_argument("item", type=int, help="the index number of the item that has either an URL or file attached")
    
    args = parser.parse_args()
    print(args)
    
    with ColorRenderer() as cr:
        tl = TodoList("todo.txt")
        
        if args.action == "list":
            for item in tl.list_items():
                if not args.search_string or args.search_string in item.text:
                    print(cr.render(item))
                    #print(item)
        elif args.action == "add":
            if not args.text:
                # TODO: insert via editor
                pass
            else:
                item = tl.add_item(args.text)
        elif args.action == "remove":
            item = tl.get_item_by_index(args.item)
            if not args.force:
                print("Do you really want to remove the following item:")
                print(cr.render(item))
                print("Please enter y/N")
                answer = raw_input().lower().strip()
                if answer == "y":
                    tl.remove_item(item)
                else:
                    print("Removing aborted")
            else:
                tl.remove_item(item)
        elif args.action == "done":
            item = tl.get_item_by_index(args.item)
            print("Marked following todo item to 'done':")
            print(cr.render(item))
            tl.set_to_done(item)
            print(cr._render(item))
        elif args.action == "reopen":
            item = tl.get_item_by_index(args.item)
            print("Setting the following todo item to open again:")
            print(cr.render(item))
            tl.reopen(item)
            print(cr.render(item))
        elif args.action == "agenda":
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
        elif args.action == "edit":
            item = tl.get_item_by_index(args.item)
            print(cr.render(item))
            tempfile = tempfile.mktemp(".txt", "todo.next")
            with open(tempfile, "w") as fp:
                fp.write(item.text)
            created = os.path.getmtime(tempfile)
            # this is platform dependent
            subprocess.call([tempfile,], shell=True)
            slept = 0.0
            WAIT_TIME = 0.2
            WAIT_MAX = 30
            while True:
                # TODO: implement http://stackoverflow.com/questions/8231719/how-to-check-whether-a-file-is-open-and-the-open-status-in-python
                # TODO: http://code.activestate.com/recipes/286238-spawning-an-editor-from-a-script/
                print("Waiting for %.0f seconds, %0.2f seconds elapsed..." % (WAIT_MAX, slept), end="\r")
                if os.path.getmtime(tempfile) != created:
                    break
                if slept >= WAIT_MAX:
                    print("Timed out, I'm tired of waiting for you. Aborting")
                    os.unlink(tempfile)
                    quit(-1)
                slept += WAIT_TIME
                time.sleep(WAIT_TIME)
            with codecs.open(tempfile, "r") as fp:
                item.text = fp.read().replace("\n", " ")
            tl.reparse_item(item)
            print(cr.render(item))
            os.unlink(tempfile)
        elif args.action == "delay":
            raise NotImplementedError()
        elif args.action == "delegated":
            raise NotImplementedError()
        elif args.action == "tasks":
            raise NotImplementedError()
        elif args.action == "overdue":
            raise NotImplementedError()
        elif args.action == "report":
            raise NotImplementedError()
        elif args.action == "archive":
            raise NotImplementedError()
        elif args.action == "clean":
            raise NotImplementedError()
        elif args.action == "open":
            raise NotImplementedError()
        
        # if we have changed something, we need to write these changes to file again
        if tl.dirty:
            print("Changes have been written")
            tl.write()