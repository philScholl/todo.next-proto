|todo| - a ``todo.txt`` command line interface
==============================================

|todo| is a command line interface for todo lists following the lightweight `todo.txt`_ syntax written in Python 2.7. 
It works on Windows and probably on Linux / MacOS as well (will check eventually - it's on my todo list ;) ).

.. contents:: Table of Contents

Installation
~~~~~~~~~~~~

1. Binary
---------

(not yet)

2. From source
--------------

Download the `sources from gitHub <https://github.com/philScholl/todo.next-proto/zipball/master>`_. You need to have
Python 2.7 with the modules `colorama <http://pypi.python.org/pypi/colorama>`_ and `dateutil <http://pypi.python.org/pypi/python-dateutil/1.5>`_ 
installed. You can then run::

    python todo.py [command] [parameters]

A good idea is to create a batch file or alias for the ``python todo.py`` part (I created a ``t.bat`` batch file 
for sake of less typing).

Differences to other todo.txt programs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Why another `todo.txt`_ program? Mainly it's about scratching my own itch, but I feel that I'm not the only one who
often wished `todo.txt`_ to have

* **Dates AND times**. All dates (e.g. due, done and created) are set using the ``key:value`` property syntax and not 
  (as done in `todo.txt`_) prepended to the todo item text. They support specifying optionally the time of a day. 
  I consider the property syntax as a good thing, as I can write them anywhere and more naturally in my todo item, preferably 
  at the end of the text, where they are not that prominently displayed.
  So, the original `todo.txt`_ syntax::
    
    x 2012-07-06 2012-07-09 @call Tommy and get his patches for +todo.next @code
  
  becomes::
  
    x @call Tommy and get his patches for +todo.next @code created:2012-07-06_13:45 done:2012-07-09_16:23
    
  Note that the time is appended to the date by an underscore. |todo| allows suppressing the unappealing properties 
  and shorten this line to::
  
    x @call Tommy and get his patches for +todo.next @code done:16:23

* **Relative dates**. Want to delay a todo item to next friday? No problem, ``delay fri`` does that. Tomorrow? Well, there
  is ``delay tm``. In one year, two weeks, two days and 13 hours? Use the ``delay +1y2w2d13h`` syntax.
* **Unique IDs**. No more line numbers, you can add (unique) IDs to todo items. This makes addressing 
  your todo items more rememberable. In fact, the default settings are so that |todo| will autogenerate unique IDs.
* **More weight on reporting**. I often want to know the things I did at some point of time. Thus, I also like to "log" 
  the things that never became todo items in the first place to this file by using *report items*.
* **Light-weight time tracking**. It is possible to *start* and *stop* working on a todo item, which will log the 
  overall duration that you worked on it.
* **Dependencies between todo items**. You can only start working on your todo after you got some input from a co-worker? 
  |todo| allows you to express that.
* **Ability to attach files, URLs and e-mail addresses**. You can attach files, URLs and e-mail addresses to todo items and open
  them via command line. Very handy.
* **Markers**. You can add any (one) character between parentheses (except priority characters A-Z) to give the todo item additional
  semantics. E.g. ``(?)`` may be an optional todo item that will be decided later on, ``(i)`` may contain important information, etc.
  Let your imagination play!
* **UTF-8 support**. If you tried several `todo.txt`-alternatives and they always crashed at your todo item to write a mail
  to Jürgen, you will know why that's important!


Todo item syntax
~~~~~~~~~~~~~~~~

The `todo.txt`_ syntax has simple rules for representing todo items:

#. One line is one todo item
#. If the line starts with "x ", it is marked as 'done', e.g. ``x call Tommy about todo.next``
#. A todo item can have the priorities ``(A)`` to ``(Z)`` (upper case) or may be not prioritized. Priorities *must* be
   stated at the beginning of the line, e.g. ``(A) feed the cat``
#. A todo item may contain multiple *projects* and *contexts*. Projects are prepended with a ``+``, contexts are prepended
   with a ``@``, neither may contain whitespace.  
#. A todo item can have multiple properties (see `Supported Properties`_). Properties' syntax is 
   ``propertyname:propertyvalue``, where neither property name nor value may contain whitespace
#. [*Note: Specific to |todo|*] If the line starts with "* ", it is a *report item*, meaning that it just 
   describes a task that was no todo item in the first place. Typically, after having
   finished a spontaneous task that I worked on, I add it as a report item, e.g. ``* called Tommy about todo.next``
#. [*Note: |todo| supports creation dates and done dates via properties, which is more fine-grained and powerful*] 
   In `todo.txt`_ syntax, creation and done date may be specified at the beginning of the line (but after the other
   prefixes)

|todo| honours the main syntax rules but, especially for creation and done dates, takes the approach that properties
are far more flexible than the syntax rules of `todo.txt`_.
   
Commands
~~~~~~~~

|todo| has multiple commands that allow viewing and manipulating your `todo.txt`_ file. On the first start (if no configuration
has been found), |todo| will guide you through the creation of a new configuration, e.g. creating a new todo file or loading
an existing one.

After you created a new todo file, you can call |todo| with the following commands:

Maintaining todo items
----------------------

:add:                   adds a new todo item to the todo list
:attach/detach:         attaches / detaches a file to / from a given todo item
:block/unblock:         manages dependencies, e.g. whether you can start working on a todo item only after having finished another item
:delay (due):           delays the due date of one or more todo items
:done (x):              sets the status of one or more todo items to 'done'
:reopen:                resets the status of a 'done' item
:edit (ed):             allows editing a given todo item
:open:                  opens either an URL, a file or mail program depending on information that is attached to the todo item
:prio:                  assigns given items a priority (absolute like 'A' or relative like '-') or removes it
:remove (rm):           removes one or more items from the todo list
:repeat:                closes a todo item and creates a copy at some specified time in future
:start / stop:          marks a todo item as *started* / *stopped*, allows time-tracking while working on todo items

Listing todo items
------------------

:agenda (ag):           displays an agenda for a given date
:age:                   displays all todo items sorted by date
:context (ctx):         lists all todo items per context
:delegated:             shows all todo items that have been delegated and wait for input
:list (ls):             lists all items that match the given expression
:lsa:                   shorthand for ``list --all``
:overdue (od):          shows all todo items that are overdue
:project (pr):          lists all todo items per project
:report (rep):          shows a daily report of all done and report items in a given time frame
:search:                lists all current and archived todo items that match the search string
:stats:                 displays some simple statistics about your todo list
:tasked:                shows all open todo items that you are tasked with

Maintaining your ``todo.txt`` file
----------------------------------

:archive:               archives all non-current todo items and removes them from todo list
:backup:                backups the current todo file to a timestamped file
:check:                 checks the todo list for syntactical validity
:config:                open |todo| configuration in editor

Supported Properties
~~~~~~~~~~~~~~~~~~~~
   
|todo| supports several properties:

:created:       date and time; automatically added to each newly created item (via ``add`` command)
:due:           date and time; the due date of the todo item
:done:          date and time; automatically added to each done item (via ``done`` command)
:id:            characters; a unique ID that is automatically added (standard configuration) to each item and can be 
                used to address a specific item
:started:       date and time; added to a todo item by the command ``start``. On ``stop`` command, the
                time difference will be calculated and stored in property ``duration``
:duration:      number; represents the time in minutes a todo item has taken to work on
:blockedby:     reference to other ID; states that this todo item depends on another item with the given ID.

Other ``todo.txt`` Resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The original `todo.txt`_ web site links a plethora of resources and examples. Especially the "Why text-based?" post is good.
* `Taskwarrior`_, a project that provides pretty similar functionality to |todo|.

.. _`todo.txt`: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format
.. _`Taskwarrior`: http://taskwarrior.org/projects/taskwarrior/
.. |todo| replace:: ``todo.next``