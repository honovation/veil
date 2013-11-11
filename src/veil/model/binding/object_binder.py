from __future__ import unicode_literals, print_function, division
import itertools
import sys
from veil.model.binding.binder_maker import compose, each
from veil.model.binding.invalid import Invalid

class ObjectBinder(object):
    def __init__(self, sub_binders, allow_missing=True, allow_extra=True):
        self.fields_binders = normalize_sub_binders(sub_binders)
        self.allow_missing = allow_missing
        self.allow_extra = allow_extra


    def __call__(self, data):
        self.assert_no_extra_no_missing(data)
        result = {}
        all_errors = {}

        for fields_names in sorted(self.fields_binders.keys(), lambda a, b: cmp(len(a), len(b))):
            binder = self.fields_binders[fields_names]
            if any(field_name in all_errors for field_name in fields_names):
                continue
            fields_data = tuple(result.get(field_name, data.get(field_name)) for field_name in fields_names)
            try:
                updated_fields_data = binder(fields_data)
            except Invalid as e:
                updated_fields_data = tuple(itertools.repeat(None, len(fields_data)))
                if e.current_error:
                    for field_name in fields_names:
                        all_errors.setdefault(field_name, []).append(e.current_error)
                else:
                    for field_name, field_errors in e.fields_errors.items():
                        all_errors.setdefault(field_name, []).extend(field_errors)
            result.update(dict(zip(fields_names, updated_fields_data)))

        if all_errors:
            raise Invalid(**all_errors)
        return result

    def assert_no_extra_no_missing(self, data):
        if not (self.allow_extra and self.allow_missing):
            actual_fields_names = set(data.keys())
            expected_fields_names = get_expected_fields_names(self.fields_binders)
            if not self.allow_extra:
                extra_fields_names = actual_fields_names.difference(expected_fields_names)
                if extra_fields_names:
                    raise Invalid(_('Extra fields found in the submitted data: {}'.format(', '.join(extra_fields_names))))
            if not self.allow_missing:
                if expected_fields_names.difference(actual_fields_names):
                    raise Invalid(_('Missing fields in the submitted data'))


def normalize_sub_binders(sub_binders):
    fields_binders = {}
    for field_or_fields, binder_or_binders in sub_binders.items():
        if isinstance(binder_or_binders, (list, tuple)):
            binders = binder_or_binders
            binder = compose(*binders)
        else:
            binder = binder_or_binders
        if isinstance(field_or_fields, (list, tuple)):
            fields = field_or_fields
        else:
            field = field_or_fields
            fields = tuple([field])
            binder = each(binder) # unbox the tuple passed in as single value
        fields_binders[fields] = binder
    return fields_binders


def get_expected_fields_names(fields_binders):
    expected_fields_names = set()
    for fields_names in fields_binders:
        for field_name in fields_names:
            expected_fields_names.add(field_name)
    return expected_fields_names


def _(*args, **kwargs):
# to supress the warning of pycharm
    return sys.modules['__builtin__']._(*args, **kwargs)
