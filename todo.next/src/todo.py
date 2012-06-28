"""

.. see:: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
import actions
from todolist import TodoList, from_date
import argparse, os, codecs, sys
import ConfigParser

if __name__ == '__main__':
    
    config_file = os.path.join(os.path.expanduser("~"), ".todonext.config")
    config = ConfigParser.ConfigParser()
    if os.path.exists(config_file):
        with codecs.open(config_file, "r", "utf-8") as fp:
            config.readfp(fp)
        todo_filename = config.get("todo", "todofile")
    else:
        # TODO: how to name new file? Where to set it up? How about changing values? Just creating example config and then open it?
        answer = raw_input("No configuration found, do you want to create a new configuration (y/N)?").lower().strip()
        if answer != "y":
            print("So, next time perhaps...")
            quit(0)
        # set todo file name
        todo_filename = "todo.txt"
        if len(sys.argv) > 1:
            todo_filename = sys.argv[1]
        todo_filename = os.path.abspath(todo_filename)
        # ask for confirmation
        answer = raw_input("Do you want to create %s (y/N)?" % todo_filename).lower().strip()
        if answer != "y":
            todo_filename = os.path.abspath(raw_input("Please enter the path/filename of your todo file: ").strip())
        print("* Trying to create a new config file at %s..." % config_file)
        with codecs.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.template"), "r", "utf-8") as fromfp:
            config.readfp(fromfp)
            print()
            config.set("todo", "todofile", todo_filename)
            with codecs.open(config_file, "w", "utf-8") as tofp:
                config.write(tofp)
        if os.path.exists(todo_filename):
            print("* Todo file %s already exists..." % todo_filename)
        else:
            print("* Creating todo file %s" % todo_filename)
            with codecs.open(todo_filename, "w", "utf-8") as fp:
                fp.write("(A) Check out https://github.com/philScholl/todo.next-proto")
        quit(0)
        
    parser = argparse.ArgumentParser(
        description="Todo.txt file CLI interface", 
        epilog="For more, see https://github.com/philScholl/todo.next-proto",
        )
    parser.add_argument("-v", action="count")
    
    subparser = parser.add_subparsers(title="subcommands", help = "sub command help", dest = "command")
    
    parse_add = subparser.add_parser("add", help=actions.get_oneliner(actions.cmd_add))
    parse_add.add_argument("text", type=str, help="the item to add", nargs="*")
    
    parse_del = subparser.add_parser("remove", help=actions.get_oneliner(actions.cmd_remove))
    parse_del.add_argument("items", type=int, help="the index number of the items to remove", nargs="+")
    parse_del.add_argument("--force", action="store_true", help="if given, confirmation is not requested")
    
    parse_list = subparser.add_parser("list", help=actions.get_oneliner(actions.cmd_list)) #, aliases=["ls"]
    parse_list.add_argument("search_string", type=str, help="a search string", nargs="?")
    parse_list.add_argument("--all", action="store_true", help="if given, also the done todo and report items are shown")
    parse_list.add_argument("--regex", action="store_true", help="if given, the search string is interpreted as a regular expression")
    
    parse_agenda = subparser.add_parser("agenda", help=actions.get_oneliner(actions.cmd_agenda))
    parse_agenda.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default 'today'", nargs="?")
    
    parse_done = subparser.add_parser("done", help=actions.get_oneliner(actions.cmd_done))
    parse_done.add_argument("items", type=int, help="the index number of the items to set to 'done'", nargs="+")
    
    parse_reopen = subparser.add_parser("reopen", help=actions.get_oneliner(actions.cmd_reopen))
    parse_reopen.add_argument("items", type=int, help="the index number of the items to reopen", nargs="+")
    
    parse_edit = subparser.add_parser("edit", help=actions.get_oneliner(actions.cmd_edit), description="This action will open an editor. If you're done editing, save the file and close the editor.")
    parse_edit.add_argument("item", type=int, help="the index number of the item to edit", nargs="?")
    
    parse_delay = subparser.add_parser("delay", help=actions.get_oneliner(actions.cmd_delay))
    parse_delay.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default '1d' (delays for 1 day)", nargs="?")
    
    parse_delegated = subparser.add_parser("delegated", help=actions.get_oneliner(actions.cmd_delegated))
    parse_delegated.add_argument("delegate", type=str, help="for filtering the name used for denoting a delegate", nargs="?")
    parse_delegated.add_argument("--all", action="store_true", help="if given, also the done todos are shown")
    
    parse_tasked = subparser.add_parser("tasked", help=actions.get_oneliner(actions.cmd_tasked))
    parse_tasked.add_argument("initiator", type=str, help="for filtering the name used for denoting the initiator", nargs="?")
    parse_tasked.add_argument("--all", action="store_true", help="if given, also the done todos are shown")
    
    parse_overdue = subparser.add_parser("overdue", help=actions.get_oneliner(actions.cmd_overdue))
    
    parse_archive = subparser.add_parser("archive", help=actions.get_oneliner(actions.cmd_archive))
    parse_archive.add_argument("to_file", type=str, help="the file where all archived todo items are appended")
    
    parse_report = subparser.add_parser("report", help=actions.get_oneliner(actions.cmd_report))
    parse_report.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default 'today'", nargs="?")
    
    #parse_clean = subparser.add_parser("clean", help=actions.get_oneliner(actions.cmd_clean))
    
    parse_open = subparser.add_parser("open", help=actions.get_oneliner(actions.cmd_open))
    parse_open.add_argument("item", type=int, help="the index number of the item that has either an URL or file attached")
    
    parse_stats = subparser.add_parser("stats", help=actions.get_oneliner(actions.cmd_stats))

    parse_project = subparser.add_parser("project", help=actions.get_oneliner(actions.cmd_project))
    parse_project.add_argument("name", type=str, help="the name of the project to display", nargs="?")
    parse_project.add_argument("--all", action="store_true", help="if given, also the done todo items are displayed")

    parse_context = subparser.add_parser("context", help=actions.get_oneliner(actions.cmd_context))
    parse_context.add_argument("name", type=str, help="the name of the context to display", nargs="?")
    parse_context.add_argument("--all", action="store_true", help="if given, also the done todo items are displayed")
    
    parse_config = subparser.add_parser("config", help=actions.get_oneliner(actions.cmd_config))
    
    parse_backup = subparser.add_parser("backup", help=actions.get_oneliner(actions.cmd_backup))
    
    args = parser.parse_args()
    # set additional data that could be interesting to actions
    args.config = config
    args.config_file = config_file
    args.todo_file = todo_filename
        
    tl = TodoList(todo_filename)

    # call the respective command
    getattr(actions, "cmd_" + args.command)(tl, args)
    
    # if we have changed something, we need to write these changes to file again
    if tl.dirty:
        tl.write()