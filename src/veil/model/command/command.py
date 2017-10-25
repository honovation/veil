from __future__ import unicode_literals, print_function, division
import functools
import logging
from collections import OrderedDict
from inspect import getargspec, isfunction
import sys
from veil.model.binding import *

LOGGER = logging.getLogger(__name__)


def command(binders):
    # syntax sugar for CommandHandlerDecorator
    if isfunction(binders):
        command_handler = binders
        return CommandHandlerDecorator()(command_handler)
    else:
        return CommandHandlerDecorator(binders)


class CommandHandlerDecorator(object):
    def __init__(self, extra_command_fields_binders=None):
        self.extra_command_fields_binders = extra_command_fields_binders

    def __call__(self, command_handler):
        if not getargspec(command_handler).args:
            raise Exception('@command should decorate command handler directly')
        command_binder = create_command_binder(command_handler, self.extra_command_fields_binders or {})

        @functools.wraps(command_handler)
        def wrapper(*positional_args, **keyword_args):
            raw_command = args_to_raw_command(positional_args, keyword_args, command_handler)
            command = raw_command_to_command(raw_command, command_binder)
            positional_args, keyword_args = command_to_args(command, command_handler)
            try:
                return command_handler(*positional_args, **keyword_args)
            except Invalid as e:
                raise InvalidCommand(e.field2error)

        wrapper.args_names = getargspec(command_handler).args
        return wrapper


def create_command_binder(command_handler, extra_command_fields_binders):
    arg_spec = getargspec(command_handler)
    binders = list(arg_spec.defaults) if arg_spec.defaults else []
    args_names = arg_spec.args
    if len(args_names) > 0 and 'self' == args_names[0]:
        binders.insert(0, anything)
    if len(binders) < len(args_names):
        binders = ([None] * (len(args_names) - len(binders))) + binders
    command_fields_binders = OrderedDict([('args', anything), ('kwargs', anything)])
    for arg_name, arg_binders in zip(args_names, binders):
        command_fields_binders[arg_name] = arg_binders
    command_fields_binders.update(extra_command_fields_binders)
    fields_without_binders = [field for field, binder in command_fields_binders.items() if not binder]
    if fields_without_binders:
        raise Exception('Must specify binder for fields {}'.format(fields_without_binders))
    command_binder = ObjectBinder(command_fields_binders)
    return command_binder


# === STEP 1: box positional/keywords into a dictionary called raw command ===
def args_to_raw_command(positional_args, keyword_args, command_handler):
    raw_command = {}
    arg_spec = getargspec(command_handler)
    args_names = arg_spec.args
    allow_extra_positional_args = arg_spec.varargs is not None
    allow_extra_keyword_args = arg_spec.keywords is not None

    if not allow_extra_positional_args and len(positional_args) > len(args_names):
        raise Exception('Extra positional fields found in the submitted data')
    args_len = min(len(args_names), len(positional_args))
    raw_command.update(dict(zip(args_names[:args_len], positional_args[:args_len])))
    extra_positional_args = positional_args[args_len:]
    raw_command['args'] = extra_positional_args

    raw_command['kwargs'] = {}
    for k, v in keyword_args.items():
        if k in args_names:
            if k in raw_command:
                raise Exception('Multiple argument for parameter {}'.format(k))
            raw_command[k] = v
        else:
            if not allow_extra_keyword_args:
                raise Exception('Extra keyword field found in the submitted data: {}'.format(k))
            raw_command['kwargs'][k] = v
    return raw_command


# === STEP 2: transform values from raw command to command ===
def raw_command_to_command(raw_command, command_binder):
    try:
        return command_binder(raw_command)
    except Invalid as e:
        raise InvalidCommand(e.field2error)


# === STEP 3: unbox command back to positional/keyword args ===
def command_to_args(command, command_handler):
    arg_spec = getargspec(command_handler)
    args_names = arg_spec.args
    positional_args = []
    for arg_name in args_names:
        positional_args.append(command[arg_name])
    positional_args.extend(command.get('args', ()))
    keyword_args = command.get('kwargs', {})
    return positional_args, keyword_args


class InvalidCommand(Exception):
    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return unicode(self).encode(encoding='UTF-8')

    def __unicode__(self):
        return ', '.join('{}: {}'.format(field_name, field_error) for field_name, field_error in self.errors.items())


def _(*args, **kwargs):
    # to supress the warning of pycharm
    return sys.modules['__builtin__']._(*args, **kwargs)
