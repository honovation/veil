from __future__ import unicode_literals, print_function, division
from datetime import datetime, date, time
import json
import decimal
from dateutil.parser import parse
from veil.utility.encoding import *


SUPPORTED_TYPES = {datetime, date, time}
assert len(SUPPORTED_TYPES) == len({c.__name__ for c in SUPPORTED_TYPES})
SUPPORTED_TYPES_NAME2CLASS = {c.__name__: c for c in SUPPORTED_TYPES}

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        type_ = type(obj)
        if type_ in SUPPORTED_TYPES:
            if type_ in {datetime, date, time}:
                return {'__type__': type_.__name__, '__value__': obj.isoformat()}
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


class CustomJSONDecoder(json.JSONDecoder):
    def __init__(self, **kw):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object, **kw)

    def dict_to_object(self, d):
        type_ = SUPPORTED_TYPES_NAME2CLASS.get(d.get('__type__'))
        if type_ in SUPPORTED_TYPES:
            if type_ in {datetime, date, time}:
                dt = parse_datetime(d.get('__value__'))
                if type_ is datetime:
                    return dt
                elif type_ is date:
                    return dt.date()
                else:
                    return dt.timetz()
        return d



def to_json(obj, **kwargs):
    return to_unicode(json.dumps(obj, cls=CustomJSONEncoder, **kwargs))


def from_json(s, **kwargs):
    return json.loads(s, cls=CustomJSONDecoder, **kwargs)



def parse_datetime(dtstr):
    return parse(dtstr, yearfirst=True)