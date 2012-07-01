"""
:mod:`cli_helpers`
~~~~~~~~~~~~~~~~~~

This module groups functionality that is needed for the Command Line Interface
version of todo.next.

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function

from colorama import init, deinit, Fore, Back, Style #@UnresolvedImport
import tempfile, subprocess, os, codecs, time, sys
from date_trans import shorten_date
import urlparse 
import re

def open_editor(filename):
    if sys.platform == "win32":
        # alternatively use os.startfile
        return subprocess.call([filename,], shell=True)
    elif sys.platform == "linux2":
        editor = os.getenv("EDITOR", "emacs")
        return os.spawnl(os.P_WAIT, editor, editor, tmpfile) #@UndefinedVariable


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
        elif sys.platform == "linux2":
            # runs only on linux
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
    def __init__(self, args = None):
        # initialize colorama
        self.args = args
        init()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb): #@UnusedVariable
        # de-initialize colorama
        deinit()
        # we don't swallow the exceptions
        return False
    
    def wrap_context(self, context):
        return Back.RED + context + Back.BLACK #@UndefinedVariable
    
    def wrap_project(self, project):
        return Back.MAGENTA + project + Back.BLACK #@UndefinedVariable
    
    def wrap_delegate(self, delegate):
        return Back.YELLOW + Style.BRIGHT + delegate + Back.BLACK + Style.NORMAL #@UndefinedVariable
    
    def wrap_prioritized(self, line):
        return Fore.WHITE + Style.BRIGHT + line + Style.RESET_ALL #@UndefinedVariable
    
    def wrap_overdue(self, line):
        return Fore.RED + Style.BRIGHT + line + Style.RESET_ALL #@UndefinedVariable
    
    def wrap_today(self, line):
        return Fore.YELLOW + Style.BRIGHT + line + Style.RESET_ALL #@UndefinedVariable
    def wrap_report(self, line):
        return Fore.CYAN + Style.DIM + line + Style.RESET_ALL  #@UndefinedVariable
    def wrap_done(self, line):
        return Fore.GREEN + Style.NORMAL + line + Style.RESET_ALL #@UndefinedVariable
    
    def clean_string(self, item):
        # if we don't have the arguments / configuration options, we cannot make assumptions here
        if not self.args:
            return item.text
        text = item.text
        conf = self.args.config
        if conf.getboolean("display", "shorten_files") and "file" in item.properties:
            file_name = item.properties.get("file") 
            if file_name:
                text = text.replace("file:%s" % file_name, "[%s]"%os.path.basename(file_name))
        if conf.getboolean("display", "shorten_urls") and item.urls:
            for url in item.urls:
                text = text.replace(url, "[%s]" % urlparse.urlsplit(url).netloc)
        if conf.getboolean("display", "shorten_due") and "due" in item.properties:
            re_replace_due = re.compile(r"\b(due:[^\s]+?)(?=$|\s)", re.UNICODE)
            text = re_replace_due.sub("due:"+shorten_date(item.properties["due"]), text)
        if conf.getboolean("display", "shorten_done") and "done" in item.properties:
            re_replace_done = re.compile(r"\b(done:[^\s]+?)(?=$|\s)", re.UNICODE)
            text = re_replace_done.sub("done:"+shorten_date(item.properties["done"]), text)
        if conf.getboolean("display", "hide_created"):
            # we nearly never need to display the created property, so hide it
            re_replace_created = re.compile(r"\b(created:[^\s]+?)(?=$|\s)")
            text = re_replace_created.sub("", text)
        return text
    
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
            listitem = "[   ] %s" % text
        else:
            listitem = "[% 3d] %s" % (item.nr, text)

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
        return listitem