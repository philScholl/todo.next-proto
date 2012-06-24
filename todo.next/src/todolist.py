"""
.. created: 22.06.2012
.. moduleauthor:: Philipp Scholl
"""

class TodoList(object):
    def __init__(self):
        self.todolist = []
        
    def add(self, listitem):
        self.todolist.append(listitem)
        
    def enumerate_items(self):
        for nr, item in enumerate(self.todolist):
            yield (nr, item)
            
    def sort_by(self, sorting_fn):
        self.todolist.sort(sorting_fn)
