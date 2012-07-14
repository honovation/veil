import shlex
import subprocess

def shell_execute(command_line, capture=False, **kwargs):
    command_args = shlex.split(command_line)
    if capture:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE))
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