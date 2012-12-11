def doc_description(help_string, description_string = None, params = None):
    def wrapped(func):
        func.__help = help_string
        func.__description = description_string if description_string else ""
        func.__params = params if params else {}
        return func
    return wrapped