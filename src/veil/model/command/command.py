from __future__ import unicode_literals, print_function, division
import functools
from inspect import getargspec, isfunction
from veil.model.binding import *
from veil.model.collection import *
from veil.utility.encoding import *


def command(binders):
# syntax sugar for CommandHandlerDecorator
    if isfunction(binders):
        command_handler = binders
        return CommandHandlerDecorator()(command_handler)
    else:
        return CommandHandlerDecorator(binders)


def command_for(command_handler, errors=None, **command_values):
    command = DictObject()
    args_names = getattr(command_handler, 'args_names', None)
    if args_names is None:
        raise Exception('{} is not command handler'.format(command_handler))
    for arg_name in args_names:
        command[arg_name] = ''
    if not errors:
        command.update(command_values or {})
    command.errors = errors or {}
    return command


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
            except Invalid, e:
                raise InvalidCommand(e.fields_errors)
            except CommandError, e:
                e.command = command
                raise


        wrapper.args_names = getargspec(command_handler).args
        return wrapper


def create_command_binder(command_handler, extra_command_fields_binders):
    arg_spec = getargspec(command_handler)
    binders = arg_spec.defaults or []
    args_names = arg_spec.args
    if len(args_names) > 0 and 'self' == args_names[0]:
        binders = [anything] + list(binders)
    if args_names and not binders:
        raise Exception('Must specify binder for all fields')
    if len(binders) < len(args_names):
        binders = ([None] * (len(args_names) - len(binders))) + list(binders)
    command_fields_binders = {
        'args': anything,
        'kwargs': anything
    }
    command_fields_binders.update(dict(zip(args_names, binders)))
    command_fields_binders.update(extra_command_fields_binders)
    for field, binder in command_fields_binders.items():
        if not binder:
            raise Exception('Must specify binder for field {}'.format(field))
    command_binder = ObjectBinder(command_fields_binders)
    return command_binder


#=== STEP 1: box positional/keywords into a dictionary called raw command ===
def args_to_raw_command(positional_args, keyword_args, command_handler):
    raw_command = {}
    arg_spec = getargspec(command_handler)
    args_names = arg_spec.args
    allow_extra_keyword_args = arg_spec.keywords is not None
    allow_extra_positional_args = arg_spec.varargs is not None

    if not allow_extra_positional_args and len(positional_args) > len(args_names):
        raise InvalidCommand(errors={None: [_('Extra fields found in the submitted data')]})
    args_len = min(len(args_names), len(positional_args))
    extra_positional_args = positional_args[args_len:]
    raw_command.update(dict(zip(args_names[:args_len], positional_args[:args_len])))
    raw_command['args'] = extra_positional_args

    raw_command['kwargs'] = {}
    for k, v in keyword_args.items():
        if k in args_names:
            if k in raw_command:
                raise Exception('Multiple argument for parameter {}'.format(k))
            raw_command[k] = v
        else:
            if not allow_extra_keyword_args:
                raise InvalidCommand(errors={None: [_('Extra fields found in the submitted data')]})
            raw_command['kwargs'][k] = v
    return raw_command


#=== STEP 2: transform values from raw command to command ===
def raw_command_to_command(raw_command, command_binder):
    try:
        return command_binder(raw_command)
    except Invalid, e:
        raise InvalidCommand(e.fields_errors)


#=== STEP 3: unbox command back to positional/keyword args ===
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
        parts = []
        for k, v in self.errors.items():
            parts.append('{}=[{}]'.format(k, ', '.join(v)))
        return to_str(', '.join(parts))


class CommandError(Exception):
    def __init__(self, message):
        super(CommandError, self).__init__()
        self.message = message
        self.command = None

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

    def __str__(self):
        return repr(self)

    def __unicode__(self, *args, **kwargs):
        return repr(self)

    def __repr__(self):
        return '{}: {}'.format(self.message or 'failed', self.command)


class NotFoundError(CommandError):
    pass


def _(*args, **kwargs):
# to supress the warning of pycharm
    from __builtin__ import _

    return _(*args, **kwargs)

def generate_signature(obj):
    if isinstance(obj, (dict, DictObject)):
        return frozenset([generate_signature(item) for item in obj.items()])
    if isinstance(obj, (tuple, list)):
        return frozenset([generate_signature(item) for item in obj])
    return obj