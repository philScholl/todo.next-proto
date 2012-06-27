"""
:mod:``
~~~~~~~~~~~~~~~~~~~~~

.. created: 25.06.2012
.. moduleauthor:: Phil <Phil@>
"""

import re

re_prio = re.compile("^\(([A-Z])\)", re.UNICODE)
re_context = re.compile("(@.*?)(?:$|\s)", re.UNICODE)
re_project = re.compile("(\+.*?)(?:$|\s)", re.UNICODE)
re_properties = re.compile("(\w*?):(.*?)(?:$|\s)", re.UNICODE)
re_delegates = re.compile("(<{2}|>{2})(.*?)(?:$|\s)", re.UNICODE)

def parse_prio(item):
    match = re_prio.match(item.text)
    if match:
        item.priority = match.group(1)
    return item

def parse_delegates(item):
    field = []
    for match in re_delegates.findall(item.text):
        field.append(match)
    if len(field) > 0:
        for mode, deleg in field:
            if mode == ">>":
                item.delegated_to.append(deleg)
            elif mode == "<<":
                item.delegated_from.append(deleg)
            else:
                # some error
                raise Exception("Parsing failed.")
    return item

def parse_project(item):
    for match in re_project.findall(item.text):
        item.projects.append(match)
    return item
    
def parse_context(item):
    for match in re_context.findall(item.text):
        item.contexts.append(match)
    return item
    
def parse_done(item):
    item.done = item.text.startswith("x ")
    return item

def parse_properties(item):
    for match in re_properties.findall(item.text):
        prop_name = match[0].lower()
        item.properties[prop_name] = match[1]
    return item

def parse_report(item):
    item.is_report = item.text.startswith("* ") 
    return item