"""

.. see:: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
import actions
from todolist import TodoList
import argparse
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Todo.txt file CLI interface", 
        epilog="For more, see https://github.com/philScholl/todo.next-proto",
        #argument_default=argparse.SUPPRESS
        )
    parser.add_argument("-v", action="count")
    
    subparser = parser.add_subparsers(title="subcommands", help = "sub command help", dest = "command")
    
    parse_add = subparser.add_parser("add", help="adds a new item to the todo list")
    parse_add.add_argument("text", type=str, help="the item to add", nargs="*")
    
    parse_del = subparser.add_parser("remove", help="removes an item from the todo list")
    parse_del.add_argument("items", type=int, help="the index number of the items to remove", nargs="+")
    parse_del.add_argument("--force", action="store_true", help="if given, confirmation is not requested")
    
    parse_list = subparser.add_parser("list", help="lists all items that match the given expression") #, aliases=["ls"]
    parse_list.add_argument("search_string", type=str, help="a search string", nargs="?")
    
    parse_agenda = subparser.add_parser("agenda", help="prints the agenda for a given date")
    parse_agenda.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default 'today'", nargs="?")
    
    parse_done = subparser.add_parser("done", help="sets a todo item to 'done' status")
    parse_done.add_argument("items", type=int, help="the index number of the items to set to 'done'", nargs="+")
    
    parse_reopen = subparser.add_parser("reopen", help="reopens a todo item already done")
    parse_reopen.add_argument("items", type=int, help="the index number of the items to reopen", nargs="+")
    
    parse_edit = subparser.add_parser("edit", help="allows editing a todo item", description="This action will open an editor. If you're done editing, save the file and close the editor.")
    parse_edit.add_argument("item", type=int, help="the index number of the item to edit", nargs="?")
    
    parse_delay = subparser.add_parser("delay", help="delays todo item's due date")
    parse_delay.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default '1d' (delays for 1 day)", nargs="?")
    
    parse_delegated = subparser.add_parser("delegated", help="shows all delegated todo items that are still open")
    parse_delegated.add_argument("delegate", type=str, help="for filtering the name used for denoting a delegate", nargs="?")
    parse_delegated.add_argument("--all", action="store_true", help="if given, also the done todos are shown")
    
    parse_tasked = subparser.add_parser("tasked", help="shows all open todo items that I am tasked with")
    parse_tasked.add_argument("initiator", type=str, help="for filtering the name used for denoting the initiator", nargs="?")
    
    parse_overdue = subparser.add_parser("overdue", help="shows all items that are overdue")
    
    parse_archive = subparser.add_parser("archive", help="archives all non-current todo items and removes them from todo.txt")
    parse_archive.add_argument("to_file", type=str, help="the file where all archived todo items are appended")
    
    parse_report = subparser.add_parser("report", help="shows a report of all done and report items")
    parse_report.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default 'today'", nargs="?")
    
    parse_clean = subparser.add_parser("clean", help="removes all outdated todo items from the todo.txt")
    
    parse_open = subparser.add_parser("open", help="opens either an URL or a file that is attached to the todo item")
    parse_open.add_argument("item", type=int, help="the index number of the item that has either an URL or file attached")
    
    parse_stats = subparser.add_parser("stats", help="displays some statistics about your 'todo.txt' file")

    parse_project = subparser.add_parser("project", help="lists all todo items per project")
    parse_project.add_argument("name", type=int, help="the name of the project to display", nargs="?")
    parse_project.add_argument("--all", action="store_true", help="if given, also the done todo items are displayed")

    parse_context = subparser.add_parser("context", help="lists all todo items per context")
    parse_context.add_argument("name", type=int, help="the name of the context to display", nargs="?")
    parse_context.add_argument("--all", action="store_true", help="if given, also the done todo items are displayed")
    
    args = parser.parse_args()
    print(args)
    
    tl = TodoList("todo.txt")

    # call the respective command
    getattr(actions, "cmd_" + args.command)(tl, args)
    
    # if we have changed something, we need to write these changes to file again
    if tl.dirty:
        tl.write()