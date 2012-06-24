"""

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
from colorama import init, deinit, Fore, Back, Style
from todolist import TodoList
import datetime
import argparse

def color_item_renderer(item):
    text = item["raw"]
    for tohi in item.get("projects", []):
        text = text.replace(tohi, Back.MAGENTA + tohi + Back.BLACK)
    for tohi in item.get("contexts", []):
        text = text.replace(tohi, Back.RED + tohi + Back.BLACK)

    prefix = ""
    if item.get("priority", None):
        prefix = Fore.WHITE + Style.BRIGHT 
    if item["done"]:
        prefix = Fore.GREEN + Style.NORMAL
    if item.get("properties", {}).get("due", datetime.datetime.now()) < datetime.datetime.now():
        prefix = Fore.RED + Style.BRIGHT
    if item.get("reportitem", False):
        prefix = Fore.CYAN + Style.DIM
    listitem = "[% 3d] %s" % (nr, text)
    return prefix + listitem + Style.RESET_ALL
    
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
    
    parse_list = subparser.add_parser("list", help="lists all items that match the given expression")
    parse_list.add_argument("search_string", type=str, help="a search string", nargs="?")
    
    
    args = parser.parse_args()
    print(args)
    init()
    tl = TodoList("todo.txt")
    
    if args.action == "list":
        for nr, item in tl.list_items():
            if not args.search_string or args.search_string in item["raw"]:
                print(color_item_renderer(item))
    elif args.action == "add":
        item = tl.add_item(args.text)
    elif args.action == "remove":
        item = tl.find_item(args.item)
        if not args.force:
            print("Do you really want to remove the following item:")
            print(color_item_renderer(item))
            print("Please enter y/N")
            # TODO: check
            tl.remove_item(args.item)
        else:
            tl.remove_item(args.item)
    if tl.dirty:
        tl.write()
    deinit()