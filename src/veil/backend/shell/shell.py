import logging
import shlex
import subprocess
import os

LOGGER = logging.getLogger(__name__)

def shell_execute(command_line, capture=False, silent=True, waits=True, **kwargs):
    command_args = shlex.split(command_line)
    if capture or silent:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE))
    if not silent:
        LOGGER.info('* exec: {}'.format(command_line))
    process = subprocess.Popen(command_args, **kwargs)
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
    if capture:
        return output
    else:
        return process


def pass_control_to(command_line):
    command_args = shlex.split(command_line)
    os.execlp(command_args[0], *command_args)


class ShellExecutionError(Exception):
    EXECUTABLE_BEFORE_COMPONENT_LOADED = 'true'
    def __init__(self, message, output=None):
        super(ShellExecutionError, self).__init__(message)
        self.output = output