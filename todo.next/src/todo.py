"""

.. see:: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
import actions
from todolist import TodoList
import argparse, os, codecs, sys
import ConfigParser

def to_unicode(string):
    return string.decode(sys.getfilesystemencoding())

def create_config_wizard():
    config = ConfigParser.ConfigParser()
    # ask for creation of configuration
    answer = raw_input("No configuration found, do you want to create a new configuration (y/N)?").lower().strip()
    if answer != "y":
        print("So, next time perhaps...")
        quit(0)
    # set standard todo file name
    todo_filename = "todo.txt"
    if len(sys.argv) > 1:
        # another configuration file has been given via the command line
        todo_filename = sys.argv[1]
    todo_filename = os.path.abspath(todo_filename)
    # ask for confirmation if the file should be created
    answer = raw_input("Do you want to create your todo file with the standard name '%s' (y/N)?" % todo_filename).lower().strip()
    if answer != "y":
        # choose an own name
        answer = raw_input("Do you want to choose another file name (y/N)?").lower().strip()
        if answer != "y":
            return None
        todo_filename = os.path.abspath(raw_input("Please enter the path/filename of your todo file: ").strip())
    if os.path.exists(todo_filename):
        print("* Todo file %s already exists..." % todo_filename)
    else:
        # create a new todo file
        print("* Creating todo file %s" % todo_filename)
        with codecs.open(todo_filename, "w", "utf-8") as fp:
            fp.write("(A) Check out https://github.com/philScholl/todo.next-proto")
    # copy the config template file and change the todo file location
    print("* Creating a new config file at '%s'" % config_file)
    with codecs.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.template"), "r", "utf-8") as fromfp:
        config.readfp(fromfp)
        config.set("todo", "todofile", todo_filename)
        with codecs.open(config_file, "w", "utf-8") as tofp:
            # save
            config.write(tofp)
    print("Please have a look at your configuration file and change according to your preferences!")
    # finish here
    return todo_filename


if __name__ == '__main__':
    # look for configuration file
    config_file = os.path.join(os.path.expanduser("~"), ".todonext.config")
    if os.path.exists(config_file):
        config = ConfigParser.ConfigParser()
        with codecs.open(config_file, "r", "utf-8") as fp:
            config.readfp(fp)
        todo_filename = config.get("todo", "todofile")
    else:
        todo_filename = create_config_wizard()
        quit(0)
        
    parser = argparse.ArgumentParser(
        description="Todo.txt file CLI interface", 
        epilog="For more, see https://github.com/philScholl/todo.next-proto",
        )
    parser.add_argument("-v", action="count")
    
    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    subparser = parser.add_subparsers(title="simple todo item management", help = "", dest = "command")
    
    parse_add = subparser.add_parser("add", help=actions.get_oneliner(actions.cmd_add))
    parse_add.add_argument("text", type=to_unicode, help="the item to add", nargs="*")
    
    parse_attach = subparser.add_parser("attach", help=actions.get_oneliner(actions.cmd_attach))
    parse_attach.add_argument("item", type=int, help="the index number of the item to which something should be attached")
    parse_attach.add_argument("location", type=str, help="either a (relative) file name or a (fully qualified) URL")
    
    parse_delay = subparser.add_parser("delay", help=actions.get_oneliner(actions.cmd_delay))
    parse_delay.add_argument("item", type=int, help="the index number of the item to delay", nargs="?")
    parse_delay.add_argument("date", type=str, help="either a date or a string like 'tomorrow', default '1d' (delays for 1 day)", nargs="?")
    parse_delay.add_argument("--force", action="store_true", help="if given, confirmation is not requested")
    
    parse_delegated = subparser.add_parser("delegated", help=actions.get_oneliner(actions.cmd_delegated))
    parse_delegated.add_argument("delegate", type=to_unicode, help="for filtering the name used for denoting a delegate", nargs="?")
    parse_delegated.add_argument("--all", action="store_true", help="if given, also the done todos are shown")
    
    parse_detach = subparser.add_parser("detach", help=actions.get_oneliner(actions.cmd_detach))
    parse_detach.add_argument("item", type=int, help="the index number of the item from which something should be detached")

    parse_done = subparser.add_parser("done", help=actions.get_oneliner(actions.cmd_done))
    parse_done.add_argument("items", type=int, help="the index number of the items to set to 'done'", nargs="+")

    parse_edit = subparser.add_parser("edit", help=actions.get_oneliner(actions.cmd_edit), description="This action will open an editor. If you're done editing, save the file and close the editor.")
    parse_edit.add_argument("item", type=int, help="the index number of the item to edit", nargs="?")

    parse_list = subparser.add_parser("list", help=actions.get_oneliner(actions.cmd_list)) #, aliases=["ls"]
    parse_list.add_argument("search_string", type=to_unicode, help="a search string", nargs="?")
    parse_list.add_argument("--all", action="store_true", help="if given, also the done todo and report items are shown")
    parse_list.add_argument("--regex", action="store_true", help="if given, the search string is interpreted as a regular expression")

    parse_open = subparser.add_parser("open", help=actions.get_oneliner(actions.cmd_open))
    parse_open.add_argument("item", type=int, help="the index number of the item that has either an URL or file attached")
    
    parse_prio = subparser.add_parser("prio", help=actions.get_oneliner(actions.cmd_prio))
    parse_prio.add_argument("items", type=int, help="the index number of the items to (re)prioritize", nargs="+")
    parse_prio.add_argument("priority", type=str, help="the new priority ('A'..'Z' or '+'/'-') or 'x' (for removing)")
    
    parse_del = subparser.add_parser("remove", help=actions.get_oneliner(actions.cmd_remove))
    parse_del.add_argument("items", type=int, help="the index number of the items to remove", nargs="+")
    parse_del.add_argument("--force", action="store_true", help="if given, confirmation is not requested")

    parse_reopen = subparser.add_parser("reopen", help=actions.get_oneliner(actions.cmd_reopen))
    parse_reopen.add_argument("items", type=int, help="the index number of the items to reopen", nargs="+")

    parse_tasked = subparser.add_parser("tasked", help=actions.get_oneliner(actions.cmd_tasked))
    parse_tasked.add_argument("initiator", type=to_unicode, help="for filtering the name used for denoting the initiator", nargs="?")
    parse_tasked.add_argument("--all", action="store_true", help="if given, also the done todos are shown")
    
    # -------------------------------------------------
    # Overview functionality
    # -------------------------------------------------

    parse_agenda = subparser.add_parser("agenda", help=actions.get_oneliner(actions.cmd_agenda))
    parse_agenda.add_argument("date", type=str, help="either a date or a string like 'tomorrow' or '*', default 'today'", nargs="?")

    parse_context = subparser.add_parser("context", help=actions.get_oneliner(actions.cmd_context))
    parse_context.add_argument("name", type=str, help="the name of the context to display", nargs="?")
    parse_context.add_argument("--all", action="store_true", help="if given, also the done todo items are displayed")
    
    parse_overdue = subparser.add_parser("overdue", help=actions.get_oneliner(actions.cmd_overdue))
    
    parse_project = subparser.add_parser("project", help=actions.get_oneliner(actions.cmd_project))
    parse_project.add_argument("name", type=str, help="the name of the project to display", nargs="?")
    parse_project.add_argument("--all", action="store_true", help="if given, also the done todo items are displayed")

    parse_report = subparser.add_parser("report", help=actions.get_oneliner(actions.cmd_report))
    parse_report.add_argument("date", type=str, help="either a date or a string like 'tomorrow' or '*', default 'today'", nargs="?")
    
    parse_search = subparser.add_parser("search", help=actions.get_oneliner(actions.cmd_search))
    parse_search.add_argument("search_string", type=to_unicode, help="a search string")
    parse_search.add_argument("--regex", action="store_true", help="if given, the search string is interpreted as a regular expression")

    parse_stats = subparser.add_parser("stats", help=actions.get_oneliner(actions.cmd_stats))

    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    parse_archive = subparser.add_parser("archive", help=actions.get_oneliner(actions.cmd_archive))
    #parse_archive.add_argument("to_file", type=str, help="the file where all archived todo items are appended", nargs="?")

    parse_backup = subparser.add_parser("backup", help=actions.get_oneliner(actions.cmd_backup))
    parse_backup.add_argument("filename", type=str, help="the name of the backup file [optional]", nargs="?")
    
    parse_check = subparser.add_parser("check", help=actions.get_oneliner(actions.cmd_check))
    
    #parse_clean = subparser.add_parser("clean", help=actions.get_oneliner(actions.cmd_clean))
    
    parse_config = subparser.add_parser("config", help=actions.get_oneliner(actions.cmd_config))
    
    
    # parse the command line parameters
    args = parser.parse_args()
    # set additional data that could be important for actions
    args.config = config
    args.config_file = config_file
    args.todo_file = todo_filename
    
    with TodoList(todo_filename) as tl:
        try:
            # call the respective command
            getattr(actions, "cmd_" + args.command)(tl, args)
        except:
            raise