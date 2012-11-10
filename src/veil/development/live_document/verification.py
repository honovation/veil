from __future__ import unicode_literals, print_function, division


def verify(value):
    return VerificationValue(value)


class VerificationValue(object):
    def __init__(self, value):
        super(VerificationValue, self).__init__()
        self.value = value

    def __eq__(self, other):
        if self.value != other:
            raise Exception('{} != {}'.format(self.value, other))

    def __gt__(self, other):
        raise NotImplementedError()

    def __ge__(self, other):
        raise NotImplementedError()

    def __lt__(self, other):
        raise NotImplementedError()

    def __le__(self, other):
        raise NotImplementedError()