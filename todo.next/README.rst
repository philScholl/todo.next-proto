todo.next - a ``todo.txt`` command line interface
=================================================

todo.next is a command line interface for todo lists following 
the lightweight `todo.txt syntax <https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format>`_ written in Python 2.7. 
It works on Windows and probably on Linux / MacOS as well.

Installation
~~~~~~~~~~~~

For now, download the `sources from gitHub <https://github.com/philScholl/todo.next-proto/zipball/master>`_. You need to have
Python 2.7 with the modules `colorama <http://pypi.python.org/pypi/colorama>`_ and `dateutil <http://pypi.python.org/pypi/python-dateutil/1.5>`_ 
installed. You can then run::

    python todo.py [command] [parameters]

A good idea is to create a batch file or alias for the ``python todo.py`` part.

When I have some more time, I will make the deployment more user friendly, promised!

Differences to todo.txt syntax
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Well, there are some:

* All dates (e.g. due, done and created) are set using the ``key:value`` property syntax and not prepended to the todo item text. I consider that 
  a good thing, as I can write them anywhere in my todo item, preferably at the end of the text, where they are not that prominent.
  So::
    
    x 2012-07-06 2012-07-09 @call Tommy and get his patches for +todonext @code
  
  looks like::
  
    x @call Tommy and get his patches for +todonext @code created:2012-07-06_13:45 done:2012-07-09_16:23
    
  However, for the CLI, you can suppress the unappealing properties and shorten this line to::
  
    x @call Tommy and get his patches for +todonext @code done:16:23
    
* IDs! You can add (unique) IDs to todo items and even autogenerate them. This makes addressing your todo items more reliable.
* Commands are slightly different to the original.
* More weight on reporting; I often want to know the things I did at some point of time. Thus, I also like to "log" the things that
  never became todo items in the first place to this file.

Usage
~~~~~

todo.next has multiple commands that allow viewing and manipulating your todo.txt file. On the first start (if no configuration
has been found), todo.next will guide you through the creation of a new configuration, e.g. creating a new todo file or loading
an existing one.

The commands:

:add:           adds a new todo item to the todo list
:attach:        attaches a file to the given todo item
:delay:         delays the due date of one or more todo items
:delegated:     shows all todo items that have been delegated and wait for input
:detach:        detaches a file from a given todo item
:done:          sets the status of one or more todo items to 'done'
:edit:          allows editing a given todo item
:list:          lists all items that match the given expression
:open:          opens either an URL, a file or mail program depending on information that is attached to the todo item
:prio:          assigns given items a priority (absolute like 'A' or relative like '-')
:remove:        removes one or more items from the todo list
:reopen:        reopens one or more items marked as 'done'
:tasked:        shows all open todo items that you are tasked with
:agenda:        displays an agenda for a given date
:context:       lists all todo items per context
:overdue:       shows all todo items that are overdue
:project:       lists all todo items per project
:report:        shows a daily report of all done and report items
:search:        lists all current and archived todo items that match the search string
:stats:         displays some simple statistics about your todo list
:archive:       archives all non-current todo items and removes them from todo list
:backup:        backups the current todo file to a timestamped file
:check:         checks the todo list for syntactical validity
:config:        open todo.next configuration in editor


Other todo.txt resources
~~~~~~~~~~~~~~~~~~~~~~~~