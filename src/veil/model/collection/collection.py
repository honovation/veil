from __future__ import unicode_literals, print_function, division

DEFAULT_PRIMARY_KEYS = ('id',)
id2obj = {}


def objectify(o):
    try:
        return _objectify(o)
    finally:
        id2obj.clear()


def _objectify(o):
    id_ = id(o)
    if id_ not in id2obj:
        if isinstance(o, Entity):
            id2obj[id_] = o
        elif isinstance(o, DictObject):
            primary_keys = o.pop('primary_keys', None)
            id2obj[id_] = Entity(o, primary_keys=primary_keys) if primary_keys else o
        elif isinstance(o, dict):
            primary_keys = o.pop('primary_keys', None)
            if primary_keys:
                id2obj[id_] = Entity(((k, _objectify(v)) for k, v in o.items()), primary_keys=primary_keys)
            else:
                id2obj[id_] = DictObject((k, _objectify(v)) for k, v in o.items())
        elif isinstance(o, (tuple, set, list)):
            id2obj[id_] = o.__class__(_objectify(e) for e in o)
        else:
            id2obj[id_] = o
    return id2obj[id_]


def entitify(o, primary_keys=True):
    try:
        return _entitify(o, primary_keys)
    finally:
        id2obj.clear()


def _entitify(o, primary_keys):
    id_ = id(o)
    if id_ not in id2obj:
        if isinstance(o, Entity):
            id2obj[id_] = o
        elif isinstance(o, (DictObject, dict)):
            primary_keys_ = o.pop('primary_keys', primary_keys)
            id2obj[id_] = Entity(((k, _entitify(v, primary_keys)) for k, v in o.items()), primary_keys=primary_keys_)
        elif isinstance(o, (tuple, set, list)):
            id2obj[id_] = o.__class__(_entitify(e, primary_keys) for e in o)
        else:
            id2obj[id_] = o
    return id2obj[id_]


def freeze_dict_object(o):
    try:
        return _freeze_dict_object(o)
    finally:
        id2obj.clear()


def _freeze_dict_object(o):
    id_ = id(o)
    if id_ not in id2obj:
        if isinstance(o, (FrozenDictObject, FrozenEntity)):
            id2obj[id_] = o
        elif isinstance(o, Entity):
            id2obj[id_] = FrozenEntity((k, _freeze_dict_object(v)) for k, v in o.items())
        elif isinstance(o, DictObject) or type(o) is dict:
            id2obj[id_] = FrozenDictObject((k, _freeze_dict_object(v)) for k, v in o.items())
        elif isinstance(o, dict):
            id2obj[id_] = o.__class__((k, _freeze_dict_object(v)) for k, v in o.items())
        elif isinstance(o, (tuple, set, list)):
            id2obj[id_] = o.__class__(_freeze_dict_object(e) for e in o)
        else:
            id2obj[id_] = o
    return id2obj[id_]


def unfreeze_dict_object(o):
    try:
        return _unfreeze_dict_object(o)
    finally:
        id2obj.clear()


def _unfreeze_dict_object(o):
    id_ = id(o)
    if id_ not in id2obj:
        if isinstance(o, FrozenEntity):
            id2obj[id_] = Entity((k, _unfreeze_dict_object(v)) for k, v in o.items())
        elif isinstance(o, FrozenDictObject) or type(o) is dict:
            id2obj[id_] = DictObject((k, _unfreeze_dict_object(v)) for k, v in o.items())
        elif isinstance(o, DictObject):
            id2obj[id_] = o
        elif isinstance(o, dict):
            id2obj[id_] = o.__class__((k, _unfreeze_dict_object(v)) for k, v in o.items())
        elif isinstance(o, (tuple, set, list)):
            id2obj[id_] = o.__class__(_unfreeze_dict_object(e) for e in o)
        else:
            id2obj[id_] = o
    return id2obj[id_]


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
    def __setattr__(self, name, value):
        raise Exception('it is frozen')

    def __setitem__(self, name, value):
        raise Exception('it is frozen')

    def __delattr__(self, name):
        raise Exception('it is frozen')

    def __delitem__(self, name):
        raise Exception('it is frozen')


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


class FrozenEntity(Entity):
    def __setattr__(self, name, value):
        if name != '_hash':
            raise Exception('it is frozen')
        super(FrozenEntity, self).__setattr__(name, value)

    def __setitem__(self, name, value):
        if name != '_hash':
            raise Exception('it is frozen')
        super(FrozenEntity, self).__setitem__(name, value)

    def __delattr__(self, name):
        if name != '_hash':
            raise Exception('it is frozen')
        super(FrozenEntity, self).__delattr__(name)

    def __delitem__(self, name):
        if name != '_hash':
            raise Exception('it is frozen')
        super(FrozenEntity, self).__delitem__(name)
