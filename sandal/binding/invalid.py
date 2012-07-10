from __future__ import unicode_literals, print_function, division

class Invalid(Exception):
    def __init__(self, current_error=None, **fields_errors):
        self.current_error = current_error
        self.fields_errors = {k: v if isinstance(v, (tuple, list, set)) else [v] for k, v in fields_errors.items()}
        super(Invalid, self).__init__()
