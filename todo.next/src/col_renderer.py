"""

.. created: 26.06.2012
.. moduleauthor:: Philipp Scholl
"""

import datetime
from colorama import init, deinit, Fore, Back, Style #@UnresolvedImport

class ColorRenderer(object):
    
    def __init__(self):
        init()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        deinit()
        # we don't swallow the exceptions
        return False
    
    def render(self, item):
        text = item.text
        for tohi in item.projects:
            text = text.replace(tohi, Back.MAGENTA + tohi + Back.BLACK) #@UndefinedVariable
        for tohi in item.contexts:
            text = text.replace(tohi, Back.RED + tohi + Back.BLACK) #@UndefinedVariable
        for tohi in item.delegated_to:
            text = text.replace(">>" + tohi, Back.YELLOW + ">>" + tohi + Back.BLACK) #@UndefinedVariable
        for tohi in item.delegated_from:
            text = text.replace("<<" + tohi, Back.YELLOW + "<<" + tohi + Back.BLACK) #@UndefinedVariable
    
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