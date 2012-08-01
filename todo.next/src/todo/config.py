"""
:mod:`config`
~~~~~~~~~~~~~



.. created: 04.07.2012
.. moduleauthor:: Phil <Phil@>
"""

class ConfigBorg(object):
    """ object implementing the Borg pattern (more pythonic Singleton)
    """
    _shared_state = {}
    
    FILE = "file"
    MAILTO = "mailto"
    DONE = "done"
    DUE = "due"
    CREATED = "created"
    STARTED = "started"
    DURATION = "duration"
    ID = "id"
    BLOCKEDBY = "blockedby"
    
    DONE_PREFIX = u"x "
    REPORT_PREFIX = u"* "
    
    DATE_PROPS = [DONE, DUE, CREATED, STARTED]
    MULTI_PROPS = [BLOCKEDBY, FILE, MAILTO]
    
    def __init__(self):
        self.__dict__ = self._shared_state
