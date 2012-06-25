import re

re_prio = re.compile("^\(([A-Z])\)", re.UNICODE)
re_context = re.compile("(@.*?)(?:$|\s)", re.UNICODE)
re_project = re.compile("(\+.*?)(?:$|\s)", re.UNICODE)
re_properties = re.compile("(\w*?):(.*?)(?:$|\s)", re.UNICODE)
re_delegates = re.compile("([(?:<<)(?:>>)]{2})(.*?)(?:$|\s)", re.UNICODE)

def parse_prio(item):
    text = item["raw"]
    match = re_prio.match(text)
    if match:
        item["priority"] = match.group(1)
    return item

def parse_delegates(item):
    text = item["raw"]
    field = []
    for match in re_delegates.findall(text):
        field.append(match)
    if len(field) > 0:
        delegates = {}
        delegates["to"] = []
        delegates["from"] = []
        for mode, deleg in field:
            if mode == ">>":
                delegates["to"].append(deleg)
            elif mode == "<<":
                delegates["from"].append(deleg)
            else:
                # some error
                print(mode, deleg, "failed")
        item["delegates"] = delegates
    return item

def parse_project(item):
    text = item["raw"]
    field = []
    for match in re_project.findall(text):
        field.append(match)
    if len(field) > 0:
        item["projects"] = field
    return item
    
def parse_context(item):
    text = item["raw"]
    field = []
    for match in re_context.findall(text):
        field.append(match)
    if len(field) > 0:
        item["contexts"] = field
    return item
    
def parse_done(item):
    text = item["raw"]
    if text.startswith("x "):
        item["done"] = True
    else:
        item["done"] = False
    return item

def parse_properties(item):
    text = item["raw"]
    props = {}
    for match in re_properties.findall(text):
        props[match[0].lower()] = match[1]
    if len(props) > 0 :
        item["properties"] = props
    return item

def parse_waiting(item):
    text = item["raw"]
    if text.startswith("< "):
        item["waiting_for_input"] = True

def parse_report(item):
    text = item["raw"]
    if text.startswith("* "):
        item["reportitem"] = True
    return item