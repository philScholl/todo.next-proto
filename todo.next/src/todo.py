#!/usr/bin/env python
"""

.. see:: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
import actions
from borg import ConfigBorg
from todolist import TodoList
from cli_helpers import get_doc_help, get_doc_param, get_doc_description, get_colors, confirm_action
import argparse, os, codecs, sys
import ConfigParser

class AliasedSubParsersAction(argparse._SubParsersAction):
    """subparser action allowing aliases for :mod:`argparse` in < Python 3.2
    
    .. see:: https://gist.github.com/471779 (credit to sampsyo)
    
    """
    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, cmd_help):
            dest = name
            if aliases:
                dest += ' (%s)' % ','.join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=cmd_help)
            

    def add_parser(self, name, **kwargs):
        if 'aliases' in kwargs:
            aliases = kwargs['aliases']
            del kwargs['aliases']
        else:
            aliases = []

        if "help" not in kwargs:
            kwargs["help"] = get_doc_help(getattr(actions, "cmd_%s" % name))
        if "description" not in kwargs:
            kwargs["description"] = get_doc_description(getattr(actions, "cmd_%s" % name))
            

        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)
        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if 'help' in kwargs:
            cmd_help = kwargs.pop('help')
            self._choices_actions.pop()
            pseudo_action = self._AliasedPseudoAction(name, aliases, cmd_help)
            self._choices_actions.append(pseudo_action)
        return parser

def to_unicode(string):
    return string.decode(sys.getfilesystemencoding())

def create_config_wizard():
    config = ConfigParser.ConfigParser()
    # ask for creation of configuration
    if not confirm_action("No configuration found, do you want to create a new configuration (y/N)?"):
        print("So, next time perhaps...")
        quit(0)
    # set standard todo file name
    todo_filename = "todo.txt"
    if len(sys.argv) > 1:
        # another configuration file has been given via the command line
        todo_filename = sys.argv[1]
    todo_filename = os.path.abspath(todo_filename)
    # ask for confirmation if the file should be created
    if not confirm_action("Do you want to create your todo file with the standard name '%s' (y/N)?" % todo_filename):
        # choose an own name
        if not confirm_action("Do you want to choose another file name (y/N)?"):
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
    print("Please have a look at your configuration file (\"t config\") and change according to your preferences!")
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
    
    # get configuration values and store them in a borg
    cconf = ConfigBorg()
    try:
        cconf.config_file = config_file
        cconf.todo_file = todo_filename
        cconf.editor = config.get("todo", "editor")
        cconf.sort = config.getboolean("todo", "sort")
        cconf.date_formats = config.get("todo", "date_formats").split()
        # are ids displayed / automatically generated?
        cconf.id_support = config.getboolean("extensions", "id_support")
        # which properties / fields are shortened
        cconf.shorten = config.get("display", "shorten").lower().split()
        # which properties / fields are suppressed
        cconf.suppress = config.get("display", "suppress").lower().split()
        # archiving and backup folders / filenames
        cconf.backup_dir = config.get("archive", "backup_dir")
        cconf.archive_unsorted_filename = config.get("archive", "archive_unsorted_filename")
        cconf.archive_filename_scheme = config.get("archive", "archive_filename_scheme")
    except ConfigParser.Error, ex:
        print("Your configuration file seems to be incorrect. Please check %s." % config_file)
        print(ex)
        quit(-1)
    
    parser = argparse.ArgumentParser(
        description="Todo.txt file CLI interface", 
        epilog="For more, see https://github.com/philScholl/todo.next-proto",
        )
    parser.register('action', 'parsers', AliasedSubParsersAction)
    
    parser.add_argument("-n", "--no-colors", action="store_true", help="suppress colored output")
    parser.add_argument("-q", "--quiet", action="store_true", help="quiet flag")
    
    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    subparser = parser.add_subparsers(title="commands", help = "", dest = "command")
    
    parse_add = subparser.add_parser("add")
    parse_add.add_argument("text", type=to_unicode, nargs="*", help=get_doc_param(actions.cmd_add, "text"))
    
    parse_attach = subparser.add_parser("attach")
    parse_attach.add_argument("item", type=str, help=get_doc_param(actions.cmd_attach, "item"))
    parse_attach.add_argument("location", type=str, help=get_doc_param(actions.cmd_attach, "location"))

    parse_call = subparser.add_parser("call")
    parse_call.add_argument("item", type=str, help=get_doc_param(actions.cmd_call, "item"))
        
    parse_delay = subparser.add_parser("delay")
    parse_delay.add_argument("item", type=str, nargs="?", help=get_doc_param(actions.cmd_delay, "item"))
    parse_delay.add_argument("date", type=str, nargs="?", help=get_doc_param(actions.cmd_delay, "date"))
    parse_delay.add_argument("-f", "--force", action="store_true", help=get_doc_param(actions.cmd_delay, "force"))
    
    parse_delegated = subparser.add_parser("delegated")
    parse_delegated.add_argument("delegate", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_delegated, "delegate"))
    parse_delegated.add_argument("-a", "--all", action="store_true", help=get_doc_param(actions.cmd_delegated, "all"))
    
    parse_detach = subparser.add_parser("detach")
    parse_detach.add_argument("item", type=str, help=get_doc_param(actions.cmd_detach, "item"))

    parse_done = subparser.add_parser("done", aliases=("x",))
    parse_done.add_argument("items", type=str, nargs="+", help=get_doc_param(actions.cmd_done, "items"))

    parse_edit = subparser.add_parser("edit", aliases=("ed",))
    parse_edit.add_argument("item", type=str, nargs="?", help=get_doc_param(actions.cmd_edit, "item"))

    parse_list = subparser.add_parser("list", aliases=("ls",))
    parse_list.add_argument("search_string", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_list, "search_string"))
    parse_list.add_argument("-a", "--all", action="store_true", help=get_doc_param(actions.cmd_list, "all"))
    parse_list.add_argument("-r", "--regex", action="store_true", help=get_doc_param(actions.cmd_list, "regex"))
    parse_list.add_argument("-c", "--ci", action="store_true", help=get_doc_param(actions.cmd_list, "ci"))

    parse_lsa = subparser.add_parser("lsa")
    parse_lsa.add_argument("search_string", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_lsa, "search_string"))
    parse_lsa.add_argument("-r", "--regex", action="store_true", help=get_doc_param(actions.cmd_lsa, "regex"))
    parse_lsa.add_argument("-c", "--ci", action="store_true", help=get_doc_param(actions.cmd_lsa, "ci"))
    
    parse_prio = subparser.add_parser("prio")
    parse_prio.add_argument("items", type=str, nargs="+", help=get_doc_param(actions.cmd_prio, "items"))
    parse_prio.add_argument("priority", type=str, help=get_doc_param(actions.cmd_prio, "priority"))
    
    parse_del = subparser.add_parser("remove", aliases=("rm", "del"))
    parse_del.add_argument("items", type=str, nargs="+", help=get_doc_param(actions.cmd_remove, "items"))
    parse_del.add_argument("-f", "--force", action="store_true", help=get_doc_param(actions.cmd_remove, "force"))

    parse_reopen = subparser.add_parser("reopen")
    parse_reopen.add_argument("items", type=str, nargs="+", help=get_doc_param(actions.cmd_reopen, "items"))

    parse_repeat = subparser.add_parser("repeat")
    parse_repeat.add_argument("item", type=str, help=get_doc_param(actions.cmd_repeat, "item"))
    parse_repeat.add_argument("date", type=str, nargs="?", help=get_doc_param(actions.cmd_repeat, "date"))
    
    parse_start = subparser.add_parser("start")
    parse_start.add_argument("item", type=str, nargs="?", help=get_doc_param(actions.cmd_start, "item"))
    
    parse_tasked = subparser.add_parser("tasked")
    parse_tasked.add_argument("initiator", type=to_unicode, nargs="?", help=get_doc_param(actions.cmd_tasked, "initiator"))
    parse_tasked.add_argument("-a", "--all", action="store_true", help=get_doc_param(actions.cmd_tasked, "all"))
    
    # -------------------------------------------------
    # Overview functionality
    # -------------------------------------------------

    parse_agenda = subparser.add_parser("agenda", aliases=("ag",))
    parse_agenda.add_argument("date", type=str, nargs="?", help=get_doc_param(actions.cmd_agenda, "date"))

    parse_context = subparser.add_parser("context", aliases=("ctx",))
    parse_context.add_argument("name", type=str, help=get_doc_param(actions.cmd_context, "name"), nargs="?")
    parse_context.add_argument("-a", "--all", action="store_true", help=get_doc_param(actions.cmd_context, "all"))
    parse_context.add_argument("-c", "--ci", action="store_true", help=get_doc_param(actions.cmd_context, "ci"))
    
    parse_mark = subparser.add_parser("mark")
    parse_mark.add_argument("marker", type=str, nargs="?", help=get_doc_param(actions.cmd_mark, "marker"))
    parse_mark.add_argument("-a", "--all", action="store_true", help=get_doc_param(actions.cmd_mark, "all"))
    
    parse_overdue = subparser.add_parser("overdue", aliases=("over", "od"))
    
    parse_project = subparser.add_parser("project", aliases=("pr",))
    parse_project.add_argument("name", type=str, nargs="?", help=get_doc_param(actions.cmd_project, "name"))
    parse_project.add_argument("-a", "--all", action="store_true", help=get_doc_param(actions.cmd_project, "all"))
    parse_project.add_argument("-c", "--ci", action="store_true", help=get_doc_param(actions.cmd_project, "ci"))
    
    parse_report = subparser.add_parser("report", aliases=("rep", ))
    parse_report.add_argument("from_date", type=str, nargs="?", help=get_doc_param(actions.cmd_report, "from_date"))
    parse_report.add_argument("to_date", type=str, nargs="?", help=get_doc_param(actions.cmd_report, "to_date"))
    
    parse_search = subparser.add_parser("search")
    parse_search.add_argument("search_string", type=to_unicode, help=get_doc_param(actions.cmd_search, "search_string"))
    parse_search.add_argument("-r", "--regex", action="store_true", help=get_doc_param(actions.cmd_search, "regex"))
    parse_search.add_argument("-c", "--ci", action="store_true", help=get_doc_param(actions.cmd_search, "ci"))

    parse_stats = subparser.add_parser("stats")

    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    parse_archive = subparser.add_parser("archive")
    #parse_archive.add_argument("to_file", type=str, help="the file where all archived todo items are appended", nargs="?")

    parse_backup = subparser.add_parser("backup")
    parse_backup.add_argument("filename", type=str, help="the name of the backup file [optional]", nargs="?")
    
    parse_check = subparser.add_parser("check")
    
    #parse_clean = subparser.add_parser("clean")
    
    parse_config = subparser.add_parser("config")
    
    
    # parse the command line parameters
    args = parser.parse_args()

    # output color handling
    cconf.no_colors = args.no_colors
    color_settings = ("col_default", "col_context", "col_project", "col_delegate", "col_id", "col_block", 
                      "col_marker", 
                      "col_item_prio", "col_item_overdue",
                      "col_item_today", "col_item_report", "col_item_done")
    # set all colors specified in the configuration file
    for color in color_settings:
        if cconf.no_colors:
            # no color flag is given
            to_col = ""
        else:
            # get color from configuration file
            try:
                to_col = get_colors(config.get("display", color))
            except ConfigParser.Error, ex:
                # TODO: log error
                to_col = ""
        setattr(cconf, color, to_col)
    
#    # set additional data that could be important for actions
#    args.config = config
#    args.config_file = config_file
#    args.todo_file = todo_filename
    
    with TodoList(todo_filename) as tl:
        try:
            # call the respective command
            getattr(actions, "cmd_" + args.command)(tl, args)
        except:
            raise