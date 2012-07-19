import logging
import shlex
import subprocess
import os

LOGGER = logging.getLogger(__name__)

def shell_execute(command_line, capture=False, silent=False, pass_control=False, **kwargs):
    command_args = shlex.split(command_line)
    if pass_control:
        os.execlp(command_args[0], *command_args)
    if capture or silent:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE))
    if not silent:
        LOGGER.info('* exec: {}'.format(command_line))
    process = subprocess.Popen(command_args, **kwargs)
    output = process.communicate()[0]
    if process.returncode:
        if capture:
            raise Exception(
                'Subprocess return code: {}, command: {}, kwargs: {}, output: {}'.format(
                    process.returncode, command_args, kwargs, output))
        else:
            raise Exception(
                'Subprocess return code: {}, command: {}, kwargs: {}'.format(
                    process.returncode, command_args, kwargs))
    if capture:
        return output
    else:
        return process