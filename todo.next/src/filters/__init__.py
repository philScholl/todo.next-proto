def filter_unprioritized(item):
    if item.get("priority", None) != None:
        return True
    return False

def filter_string(item, string):
    if string in item["raw"]:
        return True
    return False