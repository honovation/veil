from __future__ import unicode_literals, print_function, division

DEFAULT_PRIMARY_KEYS = ('id',)


def objectify(o):
    if isinstance(o, Entity):
        return o
    if isinstance(o, DictObject):
        primary_keys = o.pop('primary_keys', None)
        return Entity(o, primary_keys=primary_keys) if primary_keys else o
    elif isinstance(o, dict):
        primary_keys = o.pop('primary_keys', None)
        if primary_keys:
            return Entity({k: objectify(v) for k, v in o.items()}, primary_keys=primary_keys)
        else:
            return DictObject({k: objectify(v) for k, v in o.items()})
    elif isinstance(o, (tuple, set, list)):
        return o.__class__(objectify(e) for e in o)
    else:
        return o


def entitify(o, primary_keys=True):
    if isinstance(o, Entity):
        return o
    elif isinstance(o, (DictObject, dict)):
        primary_keys_ = o.pop('primary_keys', primary_keys)
        return Entity({k: entitify(v, primary_keys=primary_keys) for k, v in o.items()}, primary_keys=primary_keys_)
    elif isinstance(o, (tuple, set, list)):
        return o.__class__(entitify(e, primary_keys=primary_keys) for e in o)
    else:
        return o


def freeze_dict_object(o):
    if hasattr(o, 'get') and callable(getattr(o, 'get')) and o.get('_frozen'):
        return o
    if type(o) is dict:
        return freeze_dict_object(DictObject(o))
    if isinstance(o, dict):
        for v in o.values():
            freeze_dict_object(v)
        if isinstance(o, DictObject):
            o.freeze()
    elif isinstance(o, (tuple, set, list)):
        for v in o:
            freeze_dict_object(v)
    return o


def unfreeze_dict_object(o):
    if isinstance(o, DictObject) and not o.get('_frozen'):
        return o
    if isinstance(o, dict):
        for v in o.values():
            unfreeze_dict_object(v)
        if type(o) is dict:
            o = DictObject(o)
        if isinstance(o, DictObject):
            o.unfreeze()
    elif isinstance(o, (tuple, set, list)):
        for v in o:
            unfreeze_dict_object(v)
    return o


class DictObject(dict):
    def __init__(self, seq=None, **kwargs):
        super(DictObject, self).__init__(seq or (), **kwargs)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('"{}" object has no attribute "{}"'.format(self.__class__.__name__, name))

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        self._frozen = False

    def __setattr__(self, name, value):
        if self.get('_frozen') and name not in {'_frozen', '_hash'}:
            raise Exception('it is frozen')
        super(DictObject, self).__setitem__(name, value)

    def __setitem__(self, name, value):
        if self.get('_frozen') and name not in {'_frozen', '_hash'}:
            raise Exception('it is frozen')
        super(DictObject, self).__setitem__(name, value)

    def __delattr__(self, name):
        if self.get('_frozen') and name not in {'_frozen', '_hash'}:
            raise Exception('it is frozen')
        try:
            super(DictObject, self).__delitem__(name)
        except KeyError:
            raise AttributeError('"{}" object has no attribute "{}"'.format(self.__class__.__name__, name))

    def __delitem__(self, name):
        if self.get('_frozen') and name not in {'_frozen', '_hash'}:
            raise Exception('it is frozen')
        try:
            super(DictObject, self).__delitem__(name)
        except KeyError:
            raise AttributeError('"{}" object has no attribute "{}"'.format(self.__class__.__name__, name))


class Entity(DictObject):
    def __init__(self, seq=None, primary_keys=True, **kwargs):
        super(Entity, self).__init__(seq, primary_keys=DEFAULT_PRIMARY_KEYS if primary_keys is True else tuple(primary_keys), **kwargs)
        assert self.primary_keys, 'must specify primary_keys'
        if all(getattr(self, primary_key, None) is None for primary_key in self.primary_keys):
            raise Exception('{} does not have any of {}'.format(self, self.primary_keys))

    @classmethod
    def serialize(cls, **kwargs):
        kwargs.pop('_hash', None)
        return kwargs

    @classmethod
    def deserialize(cls, **kwargs):
        return cls(**kwargs)

    def clone(self, **overridden_attributes):
        serialized = self.serialize(**dict(self, **overridden_attributes))
        return self.deserialize(**serialized)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return all(getattr(self, k) == getattr(other, k) for k in self.primary_keys)

    def __hash__(self):
        if not self.get('_hash'):
            self._hash = hash(tuple(self.get(k) for k in self.primary_keys))
        return self._hash

    def __repr__(self):
        return '<{}: {}>'.format(type(self).__name__, ', '.join('{}={}'.format(k, getattr(self, k, None)) for k in self.primary_keys))
