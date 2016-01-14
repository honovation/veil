from __future__ import unicode_literals, print_function, division
import sys
from collections import OrderedDict

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
        all_field2error = {}

        for fields_names in sorted(self.fields_binders, lambda a, b: cmp(len(a), len(b))):
            binder = self.fields_binders[fields_names]
            if any(field_name in all_field2error for field_name in fields_names):
                continue
            fields_data = tuple(result.get(field_name, data.get(field_name)) for field_name in fields_names)
            try:
                updated_fields_data = binder(fields_data)
            except Invalid as e:
                if e.current_error:
                    for field_name in fields_names:
                        all_field2error[field_name] = e.current_error
                else:
                    all_field2error.update(e.field2error)
            else:
                result.update(dict(zip(fields_names, updated_fields_data)))

        if all_field2error:
            raise Invalid(**all_field2error)
        return result

    def assert_no_extra_no_missing(self, data):
        if not (self.allow_extra and self.allow_missing):
            actual_field_names = set(data)
            expected_field_names = get_expected_field_names(self.fields_binders)
            if not self.allow_extra:
                extra_field_names = actual_field_names - expected_field_names
                if extra_field_names:
                    raise Invalid(_('Extra fields found in the submitted data: {}'.format(extra_field_names)))
            if not self.allow_missing:
                missing_field_names = expected_field_names - actual_field_names
                if missing_field_names:
                    raise Invalid(_('Missing fields in the submitted data: {}'.format(missing_field_names)))


def normalize_sub_binders(sub_binders):
    fields_binders = OrderedDict()
    for field_or_fields, binder_or_binders in sub_binders.items():
        if isinstance(binder_or_binders, (list, tuple)):
            binders = binder_or_binders
            binder = compose(*binders)
        else:
            binder = binder_or_binders
        if isinstance(field_or_fields, tuple):
            fields = field_or_fields
        elif isinstance(field_or_fields, list):
            fields = tuple(field_or_fields)
        else:
            field = field_or_fields
            fields = (field,)
            binder = each(binder)  # unbox the tuple passed in as single value
        fields_binders[fields] = binder
    return fields_binders


def get_expected_field_names(fields_binders):
    return set(field_name for fields_names in fields_binders for field_name in fields_names)


def _(*args, **kwargs):
    # noinspection PyProtectedMember
    return sys.modules['__builtin__']._(*args, **kwargs)
