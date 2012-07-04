"""
:mod:``
~~~~~~~~~~~~~~~~~~~~~



.. created: 04.07.2012
.. moduleauthor:: Phil <Phil@>
"""

class ConfigBorg(object):
    _shared_state = {}
    
    def __init__(self):
        self.__dict__ = self._shared_state
