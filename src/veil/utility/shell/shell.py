from __future__ import unicode_literals, print_function, division
import shlex
import subprocess
import logging
import os

LOGGER = logging.getLogger(__name__)

def shell_execute(command_line, capture=False, waits=True, **kwargs):
    command_args = shlex.split(command_line)
    if capture:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE))
    process = subprocess.Popen(command_line if kwargs.get('shell') else command_args, **kwargs)
    if not waits:
        return process
    output = process.communicate()[0]
    if process.returncode:
        if capture:
            raise ShellExecutionError(
                'Subprocess return code: {}, command: {}, kwargs: {}, output: {}'.format(
                    process.returncode, command_args, kwargs, output), output)
        else:
            raise ShellExecutionError(
                'Subprocess return code: {}, command: {}, kwargs: {}'.format(
                    process.returncode, command_args, kwargs))
    return output


def try_shell_execute(command_line, capture=False, waits=True, **kwargs):
    try:
        shell_execute(command_line, capture=capture, waits=waits, **kwargs)
    except:
        LOGGER.info('ignored exception in shell execute', exc_info=1)
        pass


class ShellExecutionError(Exception):
    def __init__(self, message, output=None):
        super(ShellExecutionError, self).__init__(message)
        self.output = output

def pass_control_to(command_line):
    command_args = shlex.split(command_line)
    os.execlp(command_args[0], *command_args)