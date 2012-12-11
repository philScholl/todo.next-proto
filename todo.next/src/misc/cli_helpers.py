"""
:mod:`cli_helpers`
~~~~~~~~~~~~~~~~~~

This module groups functionality that is needed for the Command Line Interface
version of todo.next.

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl
"""
from __future__ import print_function

from todo.date_trans import shorten_date
from todo.config import ConfigBorg

from colorama import init, deinit, Fore, Back, Style
import re, tempfile, subprocess, os, codecs, time, urlparse, sys

# regex for finding parameters in docstring
re_docstring_param = re.compile("^\s*\*(.+?)\:(.+?)$", re.UNICODE | re.MULTILINE)
# regex for finding description
re_docstring_desc = re.compile("^\s*\:description\:(.+?)^\s*$", re.UNICODE | re.MULTILINE | re.DOTALL)

str_re_replace_prop = r"\b({prop_name}:[^\s]+?)(?=$|\s)"
prop_replace_regex_cache = {}

RESETMARKER = "#resetmarker"

def get_regex_for_replacing_prop(prop):
    if prop not in prop_replace_regex_cache:
        # create and cache
        prop_replace_regex_cache[prop] = re.compile(str_re_replace_prop.format(prop_name = prop), re.UNICODE)
    return prop_replace_regex_cache[prop]


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
    # normalize to unicode
    if isinstance(initial_text, str):
        initial_text = initial_text.decode("utf-8")
    # create a temporary text file
    tmpfile = tempfile.mktemp(".txt", "todo.next.")
    result = initial_text
    try:
        # write the initial text to this temporary file
        with codecs.open(tmpfile, "w", "utf-8") as fp:
            fp.write(initial_text.encode("utf-8"))
        
        # this is platform dependent
        if os.name == "nt":
            # to check whether the file has changed, we get the last modified time
            created = os.path.getmtime(tmpfile)
            # call the default editor
            open_editor(tmpfile)
            
            slept = 0.0
            WAIT_TIME = 0.2
            print("Waiting for saving '{fn}' (to abort, press Ctrl+C).".format(fn = tmpfile))
            while True:
                print("{sec:0.2f} seconds elapsed...".format(sec = slept), end="\r")
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


def confirm_action(text, positive=["y",]):
    answer = raw_input(text).strip().lower()
    if answer not in positive:
        return False
    return True

def suppress_if_quiet(text, args):
    if not args.quiet:
        print(text)

def input_choice(text, choices, abort = ["x", ""]):
    choices_type = type(choices[0])
    answer = raw_input(text).strip()
    return choices_type(answer)

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


    def wrap_part(self, substring, color, reset = False):
        """ wraps a substring in a todo list item with a color string 
        
        :param substring: the substring to wrap
        :type substring: str
        :param color: the color string to set for that substring
        :type color: string
        :param reset: if True, the RESETMARKER is immediately replaced by the default color again
        :type reset: bool
        :return: the wrapped substring
        :rtype: str
        """
        return color + substring + (RESETMARKER if not reset else self.conf.col_default)
    

    def wrap_line(self, line, color):
        """ wraps a whole todo list item with a color string 
        
        :param line: the line to wrap
        :type line: str
        :param color: the color string to set for that substring
        :type color: string
        :return: the color-wrapped line
        :rtype: str
        """
        line = line.replace(RESETMARKER, color)
        return color + line + self.conf.col_default        

    
    def wrap_context(self, context, reset = False):
        return self.wrap_part(context, self.conf.col_context, reset) 
    def wrap_project(self, project, reset = False):
        return self.wrap_part(project, self.conf.col_project, reset)
    def wrap_delegate(self, delegate, reset = False):
        return self.wrap_part(delegate, self.conf.col_delegate, reset)
    def wrap_id(self, tid, reset = False):
        return self.wrap_part(tid, self.conf.col_id, reset)
    def wrap_block(self, tid, reset = False):
        return self.wrap_part(tid, self.conf.col_block, reset)
    def wrap_marker(self, marker, reset = False):
        return self.wrap_part(marker, self.conf.col_marker, reset)
    
    def wrap_prioritized(self, line):
        return self.wrap_line(line, self.conf.col_item_prio)
    def wrap_overdue(self, line):
        return self.wrap_line(line, self.conf.col_item_overdue)
    def wrap_today(self, line):
        return self.wrap_line(line, self.conf.col_item_today)
    def wrap_report(self, line):
        return self.wrap_line(line, self.conf.col_item_report)
    def wrap_done(self, line):
        return self.wrap_line(line, self.conf.col_item_done)
    
    
    def clean_string(self, item):
        text = item.text
        
        for prop in item.properties:
            if prop in self.conf.shorten:
                if prop == self.conf.FILE:
                    # shorten file name
                    file_names = item.properties[prop]
                    for file_name in file_names:
                        text = text.replace(u"file:{fn}".format(fn = file_name), u"[{fn}]".format(fn = os.path.basename(file_name)))
                elif prop in (self.conf.DUE, self.conf.DONE, self.conf.CREATED, self.conf.STARTED):
                    # shorten date properties
                    text = get_regex_for_replacing_prop(prop).sub(
                        u"{prop_key}:{prop_val}".format(prop_key = prop, prop_val = shorten_date(item.properties[prop]))
                        , text) 
            if prop in self.conf.suppress:
                # remove this property
                text = get_regex_for_replacing_prop(prop).sub("", text)
        
        # urls are treated differently        
        if "url" in self.conf.shorten and item.urls:
            for url in item.urls:
                text = text.replace(url, u"[{urlbase}]".format(urlbase = urlparse.urlsplit(url).netloc))

        # remove duplicate whitespace
        return u" ".join(text.split())
    
    
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
        for tohi in item.markers:
            tohi = "({marker})".format(marker = tohi)
            text = text.replace(tohi, self.wrap_marker(tohi))
        
        if item.nr == None:
            prefix = u"[   ] "
        else:
            prefix = u"[{item_nr: 3d}] ".format(item_nr = item.nr)
        # if ids are supported and an tid exists, we replace prefix with that
        if self.conf.id_support and item.tid:
            prefix = u"[" + self.wrap_id(item.tid) + u"] "
        if self.conf.id_support and "blockedby" in item.properties:
            prefix = u"<{block}> {prefix}".format(block = self.wrap_block(",".join(sorted(item.properties["blockedby"]))), prefix = prefix)
        if self.conf.STARTED in item.properties and not item.done:
            prefix = u"{marker} {prefix}".format(marker = self.wrap_block(u"*****"), prefix = prefix)    
            
        if item.is_report:
            listitem = self.wrap_report(text)
        elif item.done:
            listitem = self.wrap_done(text)
        elif item.is_overdue():
            listitem = self.wrap_overdue(text)
        elif item.is_still_open_today():
            listitem = self.wrap_today(text)
        elif item.priority:
            listitem = self.wrap_prioritized(text)
        else:
            listitem = text
        
        listitem = u"{prefix}{item_str}".format(prefix = prefix, item_str = listitem)

        return listitem.replace(RESETMARKER, self.conf.col_default)