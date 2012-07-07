"""
:mod:`cli_helpers`
~~~~~~~~~~~~~~~~~~

This module groups functionality that is needed for the Command Line Interface
version of todo.next.

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function

from date_trans import shorten_date
from borg import ConfigBorg

from colorama import init, deinit, Fore, Back, Style
import re, tempfile, subprocess, os, codecs, time, sys, urlparse

# regex for finding parameters in docstring
re_docstring_param = re.compile("^\s*\*(.+?)\:(.+?)$", re.UNICODE | re.MULTILINE)
# regex for finding description
re_docstring_desc = re.compile("^\s*\:description\:(.+?)^\s*$", re.UNICODE | re.MULTILINE | re.DOTALL)

re_replace_created = re.compile(r"\b(created:[^\s]+?)(?=$|\s)", re.UNICODE)
re_replace_done = re.compile(r"\b(done:[^\s]+?)(?=$|\s)", re.UNICODE)
re_replace_due = re.compile(r"\b(due:[^\s]+?)(?=$|\s)", re.UNICODE)
re_replace_tid = re.compile(r"\b(id:[^\s]+?)(?=$|\s)", re.UNICODE)

RESETMARKER = "#resetmarker"

def get_colors(col_string):
    parts = col_string.upper().split()
    f, b, s = Fore.WHITE, Back.BLACK, Style.NORMAL # @UndefinedVariable
    try:
        f = f if parts[0] == "-" else getattr(Fore, parts[0])
        b = b if parts[1] == "-" else getattr(Back, parts[1])
        s = s if parts[2] == "-" else getattr(Style, parts[2])
    except:
        pass 
            
    return "".join((f, b, s))

def get_doc_description(func):
    """returns the first line and the lines prepended with ``:description:`` followed by an empty line
    
    :param func: a ``cmd_`` function
    :type func: callable
    :return: the first line + description from the docstring
    :rtype: str    
    """
    first_line = get_doc_help(func).strip()
    if not first_line.endswith("."):
        first_line += ". "
    description = ""
    for description in re_docstring_desc.findall(func.__doc__):
        break
    
    return first_line + description.strip()
    #pass
    
    
def get_doc_help(func):
    """returns the first line of the function's docstring as a help string
    
    :param func: a ``cmd_`` function
    :type func: callable
    :return: the first line of the docstring
    :rtype: str
    """
    try:
        return func.__doc__.split("\n")[0].strip()
    except:
        return "n/a"


def get_doc_param(func, param_name):
    """returns the parameter help from a function's docstring
    
    The parameter help string is searched in the docstring by looking for a line following the template
    ''* {param_name}:{description}``
    
    :param func: a ``cmd_`` function
    :type func: callable
    :param param_name: a parameter name
    :type param_name: str
    :return: the first line of the docstring
    :rtype: str
    """
    try:
        for param, desc in re_docstring_param.findall(func.__doc__):
            if param.strip() == param_name:
                return desc.strip()
        return "n/a"
    except:
        return "n/a"


def open_editor(filename):
    """opens a text editor with the specified filename
    
    :param filename: the file name to be edited
    :type filename: str
    :return: return code of the respective OS call
    :rtype: int
    """
    conf = ConfigBorg()
    if conf.editor:
        editor = conf.editor
    else:
        editor = None
    if os.name == "nt":
        if not editor:
            editor = os.getenv("EDITOR", None)
        if editor:
            return subprocess.call([editor, filename], shell=True)
        else:
            return subprocess.call([filename,], shell=True)
    elif os.name == "posix":
        if not editor:
            editor = os.getenv("EDITOR", "/etc/alternatives/editor")
        return os.spawnl(os.P_WAIT, editor, editor, tmpfile) #@UndefinedVariable


def get_editor_input(initial_text):
    """this function attempts to open an editor to allow editing a given text
    
    In *Windows*, this method will spawn the default text editor and will return
    the edited text if it detects that the file on disk has changed.
    On *Linux*, the default CLI editor is launched. 
    
    :param initial_text: the given text that can be edited
    :type initial_text: utf-8 str
    :result: the changed text
    :rtype: utf-8 encoded str
    """
    # create a temporary text file
    tmpfile = tempfile.mktemp(".txt", "todo.next.")
    result = initial_text
    try:
        # write the initial text to this temporary file
        with codecs.open(tmpfile, "w", "utf-8") as fp:
            fp.write(initial_text)
        
        # this is platform dependent
        if os.name == "nt":
            # to check whether the file has changed, we get the last modified time
            created = os.path.getmtime(tmpfile)
            # call the default editor
            open_editor(tmpfile)
            
            slept = 0.0
            WAIT_TIME = 0.2
            print("Waiting for saving %s (to abort, press Ctrl+C)." % tmpfile)
            while True:
                print("%0.2f seconds elapsed..." % slept, end="\r")
                if os.path.getmtime(tmpfile) != created:
                    # The last modified time has changed - time to end the loop
                    break
                slept += WAIT_TIME
                time.sleep(WAIT_TIME)
            with codecs.open(tmpfile, "r", "utf-8") as fp:
                result = fp.read()
        elif os.name == "posix":
            # runs only on posix
            handle = open_editor(tmpfile)
            if handle != 0:
                # an error occurred
                raise Exception("An error occurred while opening an editor.")
            else:
                with codecs.open(tmpfile, "r", "utf-8") as fp:
                    result = fp.read()
    except:
        raise
    finally:
        os.unlink(tmpfile)
    return result


class ColorRenderer(object):
    """
    """
    def __init__(self):
        self.conf = ConfigBorg()
        # initialize colorama
        init()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb): #@UnusedVariable
        # de-initialize colorama
        deinit()
        # we don't swallow the exceptions
        return False
    
    def wrap_context(self, context, reset = False):
        return self.conf.col_context + context + (RESETMARKER if not reset else self.conf.col_default) 
    
    def wrap_project(self, project, reset = False):
        return self.conf.col_project + project + (RESETMARKER if not reset else self.conf.col_default)
    
    def wrap_delegate(self, delegate, reset = False):
        return self.conf.col_delegate + delegate + (RESETMARKER if not reset else self.conf.col_default)
    
    def wrap_id(self, tid, reset = False):
        return self.conf.col_id + tid + (RESETMARKER if not reset else self.conf.col_default)
    
    def wrap_prioritized(self, line):
        line = line.replace(RESETMARKER, self.conf.col_item_prio)
        return self.conf.col_item_prio + line + self.conf.col_default
    def wrap_overdue(self, line):
        line = line.replace(RESETMARKER, self.conf.col_item_overdue)
        return self.conf.col_item_overdue + line + self.conf.col_default
    def wrap_today(self, line):
        line = line.replace(RESETMARKER, self.conf.col_item_today)
        return self.conf.col_item_today + line + self.conf.col_default
    def wrap_report(self, line):
        line = line.replace(RESETMARKER, self.conf.col_item_report)
        return self.conf.col_item_report + line + self.conf.col_default
    def wrap_done(self, line):
        line = line.replace(RESETMARKER, self.conf.col_item_done)
        return self.conf.col_item_done + line + self.conf.col_default
    
    def clean_string(self, item):
        text = item.text
        
        if "files" in self.conf.shorten and "file" in item.properties:
            file_name = item.properties.get("file") 
            if file_name:
                text = text.replace("file:%s" % file_name, "[%s]"%os.path.basename(file_name))
        if "urls" in self.conf.shorten and item.urls:
            for url in item.urls:
                text = text.replace(url, "[%s]" % urlparse.urlsplit(url).netloc)
        if "due" in self.conf.shorten and item.due_date:
            text = re_replace_due.sub("due:"+shorten_date(item.due_date), text)
        if "done" in self.conf.shorten and item.done_date:
            text = re_replace_done.sub("done:"+shorten_date(item.done_date), text)
        if "created" in self.conf.suppress and item.created_date:
            # we nearly never need to display the created property, so hide it
            text = re_replace_created.sub("", text)
        if item.tid:
            # remove in in any case
            text = re_replace_tid.sub("", text)
        
        # remove duplicate whitespace
        return " ".join(text.split())
    
    
    def render(self, item):
        """
        """
        text = self.clean_string(item)
        for tohi in item.projects:
            text = text.replace(tohi, self.wrap_project(tohi))
        for tohi in item.contexts:
            text = text.replace(tohi, self.wrap_context(tohi))
        for tohi in item.delegated_to:
            tohi = ">>" + tohi
            text = text.replace(tohi, self.wrap_delegate(tohi))
        for tohi in item.delegated_from:
            tohi = "<<" + tohi
            text = text.replace(tohi, self.wrap_delegate(tohi))
        
        if item.nr == None:
            prefix = "[   ] "
        else:
            prefix = "[% 3d] " % item.nr
        # if ids are supported and an tid exists, we replace prefix with that
        if self.conf.id_support and item.tid:
            prefix = "[" + self.wrap_id(item.tid) + "] "
            
        listitem = "%s%s" % (prefix, text)

        if item.is_report:
            return self.wrap_report(listitem)
        if item.done:
            return self.wrap_done(listitem)
        if item.is_overdue():
            return self.wrap_overdue(listitem)
        if item.is_still_open_today():
            return self.wrap_today(listitem)
        if item.priority:
            return self.wrap_prioritized(listitem)
        return listitem.replace(RESETMARKER, self.conf.col_default)