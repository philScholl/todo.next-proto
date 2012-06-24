"""

.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""
import codecs
from todolist import TodoList
from parsers import *

if __name__ == '__main__':
    tl = TodoList()
    with codecs.open("todo.txt", "r", "utf-8") as fp:
        for line in fp:
            line = line.strip()
            item = {}
            item["raw"] = line
            parse_prio(item)
            parse_context(item)
            parse_done(item)
            parse_properties(item)
            tl.add(item)
            print item