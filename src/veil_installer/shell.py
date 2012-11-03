from __future__ import unicode_literals, print_function, division
import shlex
import subprocess

def shell_execute(command_line, capture=False, waits=True, **kwargs):
    command_args = shlex.split(command_line)
    if capture:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE))
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
    return output


class ShellExecutionError(Exception):
    EXECUTABLE_BEFORE_COMPONENT_LOADED = 'true'

    def __init__(self, message, output=None):
        super(ShellExecutionError, self).__init__(message)
        self.output = output