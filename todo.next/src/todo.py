#!/usr/bin/env python
"""
todo.next
~~~~~~~~~

This is a Command Line program allowing to manage a todo list.

Further information can be found on https://github.com/philScholl/todo.next-proto/tree/master/todo.next .

For the todo file syntax and rationale, see https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format .

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
from actions import actions
from todo.config import ConfigBorg
from todo.todolist import TodoList
from misc.cli_helpers import get_colors, confirm_action
from version import program_version

import argparse, os, codecs, sys, logging
import ConfigParser

class AliasedSubParsersAction(argparse._SubParsersAction):
    """subparser action allowing aliases for :mod:`argparse` in < Python 3.2
    
    Besides that, this subparser and its arguments try to autogenerate the help
    string based on the docstrings of the ``dest`` command function.  
    
    .. see:: https://gist.github.com/471779 (credit to sampsyo)
    
    """
    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, cmd_help):
            dest = name
            if aliases:
                dest += " ({aliases})".format(aliases = ",".join(aliases))
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=cmd_help)


    def add_parser(self, name, **kwargs):
        if 'aliases' in kwargs:
            aliases = kwargs['aliases']
            del kwargs['aliases']
        else:
            aliases = []
        
        # get the function object of this action
        action_func = getattr(actions, "cmd_{cmd_name}".format(cmd_name = name))
        # create help and description strings for parser
        if "help" not in kwargs:
            kwargs["help"] = getattr(action_func, "__help", None)
        if "description" not in kwargs:
            kwargs["description"] = getattr(action_func, "__description", None)

        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)
        # save back the add_argument method
        parser._add_argument = parser.add_argument
        
        def add_argument_with_autohelp(*pname, **kwargs):
            """ helper function to replace add_argument
            
            Two cases: pname is either a string or two strings ("-"-commands).
            """
            if "help" not in kwargs:
                if len(pname) == 1:
                    norm_name = pname[0]
                else:
                    norm_name = pname[1].lstrip("-")
                kwargs["help"] = getattr(action_func, "__params", {}).get(norm_name, None)
            if len(pname) == 1:
                parser._add_argument(pname[0], **kwargs)
            else:
                parser._add_argument(pname[0], pname[1], **kwargs)
            
        # replace add_argument method
        parser.add_argument = add_argument_with_autohelp
        
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
    """ decodes a string in the file system's encoding to unicode
    """
    result = string.decode(sys.getfilesystemencoding())
    return result


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
    if not confirm_action("Do you want to create your todo file with the standard name '{fn}' (y/N)?".format(fn = todo_filename)):
        # choose an own name
        if not confirm_action("Do you want to choose another file name (y/N)?"):
            return None
        todo_filename = os.path.abspath(raw_input("Please enter the path/filename of your todo file: ").strip())
    if os.path.exists(todo_filename):
        print("* Todo file {fn} already exists...".format(fn = todo_filename))
    else:
        # create a new todo file
        print("* Creating todo file {fn}".format(fn = todo_filename))
        with codecs.open(todo_filename, "w", "utf-8") as fp:
            fp.write("(A) Check out https://github.com/philScholl/todo.next-proto")
    # copy the config template file and change the todo file location
    print("* Creating a new config file at '{fn}'".format(fn = config_file))
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
    logger = logging.getLogger("todonext")
    logger.setLevel(logging.ERROR)
    #logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(handler)

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
        print("Your configuration file seems to be incorrect. Please check '{fn}'.".format(fn = config_file))
        print(ex)
        quit(-1)
    
    parser = argparse.ArgumentParser(
        description="Todo.txt file CLI interface", 
        epilog="For more, see https://github.com/philScholl/todo.next-proto",
        )
    parser.register('action', 'parsers', AliasedSubParsersAction)
    
    parser.add_argument("-n", "--no-colors", action="store_true", help="suppress colored output")
    parser.add_argument("-q", "--quiet", action="store_true", help="quiet flag")
    parser.add_argument("-v", "--version", action="version", version="todo.next v. {version}".format(version = program_version))
    
    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    subparser = parser.add_subparsers(title="commands", help = "", dest = "command")
    
    parse_add = subparser.add_parser("add")
    parse_add.add_argument("text", type=to_unicode, nargs="*")
    
    parse_age = subparser.add_parser("age")
    parse_age.add_argument("desc", type=bool, default=False, nargs="?")
    parse_age.add_argument("-a", "--all", action="store_true")
    
    parse_attach = subparser.add_parser("attach")
    parse_attach.add_argument("item", type=to_unicode)
    parse_attach.add_argument("location", type=to_unicode)
    
    if cconf.id_support:
        parse_block= subparser.add_parser("block")
        parse_block.add_argument("item", type=to_unicode)
        parse_block.add_argument("blocked", type=to_unicode)
    
        parse_unblock= subparser.add_parser("unblock")
        parse_unblock.add_argument("item", type=to_unicode)
        parse_unblock.add_argument("blocked", type=to_unicode)

    parse_call = subparser.add_parser("call")
    parse_call.add_argument("item", type=to_unicode)
        
    parse_delay = subparser.add_parser("delay", aliases=("due",))
    parse_delay.add_argument("item", type=to_unicode, nargs="?")
    parse_delay.add_argument("date", type=to_unicode, nargs="?")
    parse_delay.add_argument("-f", "--force", action="store_true")
    
    parse_delegated = subparser.add_parser("delegated")
    parse_delegated.add_argument("delegate", type=to_unicode, nargs="?")
    parse_delegated.add_argument("-a", "--all", action="store_true")
    
    parse_detach = subparser.add_parser("detach")
    parse_detach.add_argument("item", type=to_unicode)

    parse_done = subparser.add_parser("done", aliases=("x",))
    parse_done.add_argument("items", type=to_unicode, nargs="+")

    parse_edit = subparser.add_parser("edit", aliases=("ed",))
    parse_edit.add_argument("item", type=to_unicode, nargs="?")

    parse_list = subparser.add_parser("list", aliases=("ls",))
    parse_list.add_argument("search_string", type=to_unicode, nargs="?")
    parse_list.add_argument("-a", "--all", action="store_true")
    parse_list.add_argument("-r", "--regex", action="store_true")
    parse_list.add_argument("-c", "--ci", action="store_true")

    parse_lsa = subparser.add_parser("lsa")
    parse_lsa.add_argument("search_string", type=to_unicode, nargs="?")
    parse_lsa.add_argument("-r", "--regex", action="store_true")
    parse_lsa.add_argument("-c", "--ci", action="store_true")
    
    parse_prio = subparser.add_parser("prio")
    parse_prio.add_argument("items", type=to_unicode, nargs="+")
    parse_prio.add_argument("priority", type=str)
    
    parse_del = subparser.add_parser("remove", aliases=("rm",))
    parse_del.add_argument("items", type=to_unicode, nargs="+")
    parse_del.add_argument("-f", "--force", action="store_true")

    parse_reopen = subparser.add_parser("reopen")
    parse_reopen.add_argument("items", type=to_unicode, nargs="+")

    parse_repeat = subparser.add_parser("repeat")
    parse_repeat.add_argument("item", type=to_unicode)
    parse_repeat.add_argument("date", type=to_unicode, nargs="?")
    
    parse_start = subparser.add_parser("start")
    parse_start.add_argument("item", type=to_unicode, nargs="?")

    parse_start = subparser.add_parser("stop")
    parse_start.add_argument("item", type=to_unicode)
    
    parse_tasked = subparser.add_parser("tasked")
    parse_tasked.add_argument("initiator", type=to_unicode, nargs="?")
    parse_tasked.add_argument("-a", "--all", action="store_true")
    
    # -------------------------------------------------
    # Overview functionality
    # -------------------------------------------------

    parse_agenda = subparser.add_parser("agenda", aliases=("ag",))
    parse_agenda.add_argument("date", type=to_unicode, nargs="?")

    parse_context = subparser.add_parser("context", aliases=("ctx",))
    parse_context.add_argument("name", type=to_unicode, nargs="?")
    parse_context.add_argument("-a", "--all", action="store_true")
    parse_context.add_argument("-c", "--ci", action="store_true")
    
    parse_mark = subparser.add_parser("mark")
    parse_mark.add_argument("marker", type=to_unicode, nargs="?")
    parse_mark.add_argument("-a", "--all", action="store_true")
    
    parse_overdue = subparser.add_parser("overdue", aliases=("over", "od"))
    
    parse_project = subparser.add_parser("project", aliases=("pr",))
    parse_project.add_argument("name", type=to_unicode, nargs="?")
    parse_project.add_argument("-a", "--all", action="store_true")
    parse_project.add_argument("-c", "--ci", action="store_true")
    
    parse_report = subparser.add_parser("report", aliases=("rep", ))
    parse_report.add_argument("from_date", type=to_unicode, nargs="?")
    parse_report.add_argument("to_date", type=to_unicode, nargs="?")
    
    parse_search = subparser.add_parser("search")
    parse_search.add_argument("search_string", type=to_unicode)
    parse_search.add_argument("-r", "--regex", action="store_true")
    parse_search.add_argument("-c", "--ci", action="store_true")

    parse_stats = subparser.add_parser("stats")

    # -------------------------------------------------
    # Maintenance functionality
    # -------------------------------------------------
    
    parse_archive = subparser.add_parser("archive")
    #parse_archive.add_argument("to_file", type=to_unicode, nargs="?")

    parse_backup = subparser.add_parser("backup")
    parse_backup.add_argument("filename", type=to_unicode, nargs="?")
    
    parse_check = subparser.add_parser("check")
    
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
                logger.warning("Configuration does not have a '{val}' value defined".format(color))
                to_col = ""
        setattr(cconf, color, to_col)
        
    with TodoList(todo_filename) as tl:
        try:
            # call the respective command
            getattr(actions, "cmd_" + args.command)(tl, args)
        except:
            raise