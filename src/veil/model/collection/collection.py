from __future__ import unicode_literals, print_function, division


def filter_single_or_none(collection, criteria):
    return single_or_none(filter(criteria, collection))


def single_or_none(collection):
    length = len(collection)
    if length == 0:
        return None
    elif length == 1:
        return collection[0]
    else:
        raise Exception('more than one element in collection: {}'.format(collection))


def filter_single(collection, criteria):
    return single(filter(criteria, collection))


def single(collection):
    length = len(collection)
    if length == 0:
        raise Exception('no element in collection')
    elif length == 1:
        return collection[0]
    else:
        raise Exception('more than one element in collection: {}'.format(collection))


def filter_first_or_none(collection, criteria):
    return first_or_none(filter(criteria, collection))


def first_or_none(collection):
    return collection[0] if collection else None


def filter_first(collection, criteria):
    return first(filter(criteria, collection))


def first(collection):
    if not collection:
        raise Exception('no element in collection')
    return collection[0]


def objectify(o):
    if isinstance(o, DictObject):
        return o
    elif isinstance(o, dict):
        return DictObject({k: objectify(v) for k, v in o.items()})
    elif isinstance(o, (tuple, set, list)):
        return [objectify(e) for e in o]
    else:
        return o


def entitify(o, primary_keys=None):
    if isinstance(o, Entity):
        return o
    elif isinstance(o, (dict, DictObject)):
        return Entity({k: entitify(v, primary_keys=primary_keys) for k, v in o.items()}, primary_keys=primary_keys)
    elif isinstance(o, (tuple, set, list)):
        return [entitify(e, primary_keys=primary_keys) for e in o]
    else:
        return o


def freeze_dict_object(o):
    if isinstance(o, FrozenDictObject):
        return o
    elif isinstance(o, dict):
        return FrozenDictObject({k: freeze_dict_object(v) for k, v in o.items()})
    elif isinstance(o, (tuple, set, list)):
        return [freeze_dict_object(e) for e in o]
    else:
        return o


class DictObject(dict):
    def __init__(self, seq=None, **kwargs):
        super(DictObject, self).__init__(seq or (), **kwargs)

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('"{}" object has no attribute "{}"'.format(self.__class__.__name__, name))

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError('"{}" object has no attribute "{}"'.format(self.__class__.__name__, name))


class FrozenDictObject(DictObject):
    def __setattr__(self, key, value):
        raise Exception('it is frozen')

    def __setitem__(self, key, value):
        raise Exception('it is frozen')


class Entity(DictObject):
    def __init__(self, seq=None, primary_keys=None, **kwargs):
        super(Entity, self).__init__(seq, **kwargs)
        self.primary_keys = primary_keys or ('id',)
        assert self.primary_keys, 'must specify primary_keys'
        if all(getattr(self, primary_key, None) is None for primary_key in self.primary_keys):
            raise Exception('{} does not have any of {}'.format(self, self.primary_keys))

    @classmethod
    def serialize(cls, **kwargs):
        if '_hash' in kwargs:
            del kwargs['_hash']
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