from __future__ import unicode_literals, print_function, division
from veil.model.collection import DictObject

class Consts(DictObject):
    def __setattr__(self, name, value):
        if not is_const(value):
            raise Exception('{} is not const'.format(value))
        return super(Consts, self).__setattr__(name, value)

    def __setitem__(self, key, value):
        if not is_const(value):
            raise Exception('{} is not const'.format(value))
        return super(Consts, self).__setitem__(key, value)


def is_const(value):
    if isinstance(value, basestring):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return True
    if isinstance(value, tuple):
        return all([is_const(e) for e in value])
    if isinstance(value, dict):
        return all([is_const(e) for e in value.keys()]) and all([is_const(e) for e in value.values()])
    return False

consts = Consts()

def def_const(**kwargs):
    assert len(kwargs) == 1
    consts.update(kwargs)
    return kwargs.values()[0]