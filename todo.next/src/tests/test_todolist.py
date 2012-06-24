"""
:mod:``
~~~~~~~~~~~~~~~~~~~~~

.. created: 24.06.2012
.. moduleauthor:: Phil <Phil@>
"""
from unittest2 import TestCase
from todolist import TodoList
import datetime

class TestTodolist(TestCase):
    
    def setUp(self):
        TestCase.setUp(self)
        self.tl = TodoList("todo.txt")
    
    def test_dateparser(self):
        tests = ["today", "tomorrow", "2012-02-28_17", "21.4.", "17:30"]
        for i in tests:
            assert isinstance(self.tl.to_date(i), datetime.datetime)  
