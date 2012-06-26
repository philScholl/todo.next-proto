"""
:mod:`cli_helpers`
~~~~~~~~~~~~~~~~~~

This module groups functionality that is needed for the Command Line Interface
version of todo.next.

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function
import datetime
from colorama import init, deinit, Fore, Back, Style #@UnresolvedImport
import tempfile, subprocess, os, codecs, time, sys


def get_editor_input(initial_text):
    """this function attempts to open an editor to allow editing a given text
    
    In *Windows*, this method will spawn the default text editor and will return
    the edited text if it detects that the file on disk has changed.
    On *Linux*, the default CLI editor is launched. 
    
    :param initial_text: the given text that can be edited
    :type initial_text: utf-8 str
    :result: the changed text
    :rtype: utf-8 str
    """
    # create a temporary text file
    tmpfile = tempfile.mktemp(".txt", "todo.next.")
    result = initial_text
    try:
        # write the initial text to this temporary file
        with codecs.open(tmpfile, "w", "utf-8") as fp:
            fp.write(initial_text)
        
        # this is platform dependent
        if sys.platform == "win32":
            # to check whether the file has changed, we get the last modified time
            created = os.path.getmtime(tmpfile)
            # call the default editor
            subprocess.call([tmpfile,], shell=True)
            
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
        elif sys.platform == "linux2":
            # runs only on linux
            editor = os.getenv("EDITOR", "emacs")
            handle = os.spawnl(os.P_WAIT, editor, editor, tmpfile) #@UndefinedVariable
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
        # initialize colorama
        init()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb): #@UnusedVariable
        # de-initialize colorama
        deinit()
        # we don't swallow the exceptions
        return False
    
    def render(self, item):
        """
        """
        text = item.text
        for tohi in item.projects:
            text = text.replace(tohi, Back.MAGENTA + tohi + Back.BLACK) #@UndefinedVariable
        for tohi in item.contexts:
            text = text.replace(tohi, Back.RED + tohi + Back.BLACK) #@UndefinedVariable
        for tohi in item.delegated_to:
            text = text.replace(">>" + tohi, Back.YELLOW + Style.BRIGHT + ">>" + tohi + Back.BLACK + Style.NORMAL) #@UndefinedVariable
        for tohi in item.delegated_from:
            text = text.replace("<<" + tohi, Back.YELLOW + Style.BRIGHT + "<<" + tohi + Back.BLACK + Style.NORMAL) #@UndefinedVariable
    
        prefix = ""
        now = datetime.datetime.now()
        if item.priority:
            prefix = Fore.WHITE + Style.BRIGHT #@UndefinedVariable
        if item.due_date:
            # due date is set
            if datetime.datetime(year=item.due_date.year, month=item.due_date.month, day=item.due_date.day) == \
                datetime.datetime(year=now.year, month=now.month, day=now.day):
                if (item.due_date.hour, item.due_date.minute) == (0, 0): 
                    # item is due today on general day
                    prefix = Fore.YELLOW + Style.BRIGHT #@UndefinedVariable
                elif item.due_date > now:
                    # due date is today but will be later on
                    prefix = Fore.YELLOW + Style.BRIGHT #@UndefinedVariable
                else:
                    # due date has already happened today
                    prefix = Fore.RED + Style.BRIGHT #@UndefinedVariable
            elif item.due_date < now:
                prefix = Fore.RED + Style.BRIGHT #@UndefinedVariable
        if item.is_report:
            prefix = Fore.CYAN + Style.DIM #@UndefinedVariable
        if item.done:
            prefix = Fore.GREEN + Style.NORMAL #@UndefinedVariable
        listitem = "[% 3d] %s" % (item.nr, text)
        return prefix + listitem + Style.RESET_ALL #@UndefinedVariable