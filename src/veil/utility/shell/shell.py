from __future__ import unicode_literals, print_function, division
import shlex
import subprocess
import logging
import os
from veil.utility.encoding import *

LOGGER = logging.getLogger(__name__)


def shell_execute(command_line, capture=False, waits=True, shell=True, debug=False, expected_return_codes=(0,), depress_log=False, **kwargs):
    if debug:
        LOGGER.debug('shell execute: %(command_line)s', {'command_line': command_line})
    if capture:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE))
    command_args = command_line if shell else shlex.split(command_line)
    try:
        process = subprocess.Popen(command_args, shell=shell, **kwargs)
    except Exception:
        LOGGER.exception('failed to invoke: %(command_args)s, %(kwargs)s', {'command_args': command_args, 'kwargs': kwargs})
        raise
    if not waits:
        return process
    output = to_unicode(process.communicate()[0])
    if capture and output:
        output = output.strip()
    if process.returncode not in expected_return_codes:
        if not depress_log:
            LOGGER.warn('received nonzero return code: %(return_code)s, %(command_line)s, %(kwargs)s, %(output)s', {
                'return_code': process.returncode,
                'command_line': command_line,
                'kwargs': kwargs,
                'output': output
            })
        if capture:
            raise ShellExecutionError(
                'Subprocess return code: {}, command: {}, kwargs: {}, output: {}'.format(process.returncode, command_args, kwargs, output), output)
        else:
            raise ShellExecutionError('Subprocess return code: {}, command: {}, kwargs: {}'.format(process.returncode, command_args, kwargs))
    return output


def try_shell_execute(command_line, capture=False, waits=True, shell=True, **kwargs):
    try:
        return shell_execute(command_line, capture=capture, waits=waits, shell=shell, **kwargs)
    except ShellExecutionError:
        LOGGER.warn('ignored exception in shell execute', exc_info=1)


def pass_control_to(command_line):
    command_args = shlex.split(command_line)
    os.execlp(command_args[0], *command_args)


class ShellExecutionError(Exception):
    def __init__(self, message, output=None):
        super(ShellExecutionError, self).__init__(message)
        self.output = output
