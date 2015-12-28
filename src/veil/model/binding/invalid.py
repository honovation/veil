from __future__ import unicode_literals, print_function, division


class Invalid(Exception):
    def __init__(self, current_error=None, **field2error):
        super(Invalid, self).__init__()
        self.current_error = current_error
        self.field2error = field2error
