"""

.. see:: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
import actions
from borg import ConfigBorg
from todolist import TodoList
from cli_helpers import get_doc_help, get_doc_param, get_doc_description
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
    parser.add_argument("-v", action="count", help="verbose flag")
    
    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    subparser = parser.add_subparsers(title="commands", help = "", dest = "command")
    
    parse_add = subparser.add_parser("add", help=get_doc_help(actions.cmd_add), description=get_doc_description(actions.cmd_add))
    parse_add.add_argument("text", type=to_unicode, nargs="*", help=get_doc_param(actions.cmd_add, "text"))
    
    parse_attach = subparser.add_parser("attach", help=get_doc_help(actions.cmd_attach), description=get_doc_description(actions.cmd_attach))
    parse_attach.add_argument("item", type=int, help=get_doc_param(actions.cmd_attach, "item"))
    parse_attach.add_argument("location", type=str, help=get_doc_param(actions.cmd_attach, "location"))
    
    parse_delay = subparser.add_parser("delay", help=get_doc_help(actions.cmd_delay), description=get_doc_description(actions.cmd_delay))
    parse_delay.add_argument("item", type=int, nargs="?", help=get_doc_param(actions.cmd_delay, "item"))
    parse_delay.add_argument("date", type=str, nargs="?", help=get_doc_param(actions.cmd_delay, "date"))
    parse_delay.add_argument("--force", action="store_true", help=get_doc_param(actions.cmd_delay, "force"))
    
    parse_delegated = subparser.add_parser("delegated", help=get_doc_help(actions.cmd_delegated), description=get_doc_description(actions.cmd_delegated))
    parse_delegated.add_argument("delegate", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_delegated, "delegate"))
    parse_delegated.add_argument("--all", action="store_true", help=get_doc_param(actions.cmd_delegated, "all"))
    
    parse_detach = subparser.add_parser("detach", help=get_doc_help(actions.cmd_detach), description=get_doc_description(actions.cmd_detach))
    parse_detach.add_argument("item", type=int, help=get_doc_param(actions.cmd_detach, "item"))

    parse_done = subparser.add_parser("done", help=get_doc_help(actions.cmd_done), description=get_doc_description(actions.cmd_done))
    parse_done.add_argument("items", type=int, nargs="+", help=get_doc_param(actions.cmd_done, "items"))

    parse_edit = subparser.add_parser("edit", help=get_doc_help(actions.cmd_edit), description=get_doc_description(actions.cmd_edit))
    parse_edit.add_argument("item", type=int, nargs="?", help=get_doc_param(actions.cmd_edit, "item"))

    parse_list = subparser.add_parser("list", help=get_doc_help(actions.cmd_list), description=get_doc_description(actions.cmd_list)) #, aliases=["ls"]
    parse_list.add_argument("search_string", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_list, "search_string"))
    parse_list.add_argument("--all", action="store_true", help=get_doc_param(actions.cmd_list, "all"))
    parse_list.add_argument("--regex", action="store_true", help=get_doc_param(actions.cmd_list, "regex"))

    parse_open = subparser.add_parser("open", help=get_doc_help(actions.cmd_open), description=get_doc_description(actions.cmd_open))
    parse_open.add_argument("item", type=int, help=get_doc_param(actions.cmd_open, "item"))
    
    parse_prio = subparser.add_parser("prio", help=get_doc_help(actions.cmd_prio), description=get_doc_description(actions.cmd_prio))
    parse_prio.add_argument("items", type=int, nargs="+", help=get_doc_param(actions.cmd_prio, "items"))
    parse_prio.add_argument("priority", type=str, help=get_doc_param(actions.cmd_prio, "priority"))
    
    parse_del = subparser.add_parser("remove", help=get_doc_help(actions.cmd_remove), description=get_doc_description(actions.cmd_remove))
    parse_del.add_argument("items", type=int, nargs="+", help=get_doc_param(actions.cmd_remove, "items"))
    parse_del.add_argument("--force", action="store_true", help=get_doc_param(actions.cmd_remove, "force"))

    parse_reopen = subparser.add_parser("reopen", help=get_doc_help(actions.cmd_reopen), description=get_doc_description(actions.cmd_reopen))
    parse_reopen.add_argument("items", type=int, nargs="+", help=get_doc_param(actions.cmd_reopen, "items"))

    parse_tasked = subparser.add_parser("tasked", help=get_doc_help(actions.cmd_tasked), description=get_doc_description(actions.cmd_tasked))
    parse_tasked.add_argument("initiator", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_tasked, "initiator"))
    parse_tasked.add_argument("--all", action="store_true", help=get_doc_param(actions.cmd_tasked, "all"))
    
    # -------------------------------------------------
    # Overview functionality
    # -------------------------------------------------

    parse_agenda = subparser.add_parser("agenda", help=get_doc_help(actions.cmd_agenda), description=get_doc_description(actions.cmd_agenda))
    parse_agenda.add_argument("date", type=str, nargs="?", help=get_doc_param(actions.cmd_agenda, "date"))

    parse_context = subparser.add_parser("context", help=get_doc_help(actions.cmd_context), description=get_doc_description(actions.cmd_context))
    parse_context.add_argument("name", type=str, help=get_doc_param(actions.cmd_context, "name"), nargs="?")
    parse_context.add_argument("--all", action="store_true", help=get_doc_param(actions.cmd_context, "all"))
    
    parse_overdue = subparser.add_parser("overdue", help=get_doc_help(actions.cmd_overdue), description=get_doc_description(actions.cmd_overdue))
    
    parse_project = subparser.add_parser("project", help=get_doc_help(actions.cmd_project), description=get_doc_description(actions.cmd_project))
    parse_project.add_argument("name", type=str, nargs="?", help=get_doc_param(actions.cmd_project, "name"))
    parse_project.add_argument("--all", action="store_true", help=get_doc_param(actions.cmd_project, "all"))

    parse_report = subparser.add_parser("report", help=get_doc_help(actions.cmd_report), description=get_doc_description(actions.cmd_report))
    parse_report.add_argument("date", type=str, nargs="?", help=get_doc_param(actions.cmd_report, "date"))
    
    parse_search = subparser.add_parser("search", help=get_doc_help(actions.cmd_search), description=get_doc_description(actions.cmd_search))
    parse_search.add_argument("search_string", type=to_unicode, help=get_doc_param(actions.cmd_search, "search_string"))
    parse_search.add_argument("--regex", action="store_true", help=get_doc_param(actions.cmd_search, "regex"))

    parse_stats = subparser.add_parser("stats", help=get_doc_help(actions.cmd_stats), description=get_doc_description(actions.cmd_stats))

    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    parse_archive = subparser.add_parser("archive", help=get_doc_help(actions.cmd_archive), description=get_doc_description(actions.cmd_archive))
    #parse_archive.add_argument("to_file", type=str, help="the file where all archived todo items are appended", nargs="?")

    parse_backup = subparser.add_parser("backup", help=get_doc_help(actions.cmd_backup), description=get_doc_description(actions.cmd_backup))
    parse_backup.add_argument("filename", type=str, help="the name of the backup file [optional]", nargs="?")
    
    parse_check = subparser.add_parser("check", help=get_doc_help(actions.cmd_check), description=get_doc_description(actions.cmd_check))
    
    #parse_clean = subparser.add_parser("clean", help=get_doc_help(actions.cmd_clean), description=get_doc_description(actions.cmd_clean))
    
    parse_config = subparser.add_parser("config", help=get_doc_help(actions.cmd_config), description=get_doc_description(actions.cmd_config))
    
    
    # parse the command line parameters
    args = parser.parse_args()
#    # set additional data that could be important for actions
#    args.config = config
#    args.config_file = config_file
#    args.todo_file = todo_filename
    
    cconf = ConfigBorg()
    cconf.id_support = config.getboolean("extensions", "id_support")
    cconf.config_file = config_file
    cconf.todo_file = todo_filename
    cconf.shorten = config.get("display", "shorten").lower().split()
    cconf.suppress = config.get("display", "suppress").lower().split()
    cconf.backup_dir = config.get("archive", "backup_dir")
    cconf.archive_unsorted_filename = config.get("archive", "archive_unsorted_filename")
    cconf.archive_filename_scheme = config.get("archive", "archive_filename_scheme")
    
    with TodoList(todo_filename) as tl:
        try:
            # call the respective command
            getattr(actions, "cmd_" + args.command)(tl, args)
        except:
            raise