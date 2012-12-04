from __future__ import unicode_literals, print_function, division
import sys
import shlex
import os.path
import os
import subprocess


def main():
    installer_path = sys.argv[1]

    install_git()
    clone_veil()
    pull_veil()
    install(installer_path)
    mark_installed(installer_path)


def install_git():
    shell_execute('apt-get install -y git-core')


def clone_veil():
    if os.path.exists('/opt/veil'):
        return
    shell_execute('git clone git://github.com/honovation/veil.git /opt/veil')


def pull_veil():
    shell_execute('git pull', cwd='/opt/veil')


def install(installer_path):
    shell_execute('/opt/veil/bin/veil init', cwd='/opt/veil')
    env = os.environ.copy()
    env['VEIL_DEPENDENCY_MIRROR'] = 'http://10.0.3.99:80'
    shell_execute('veil install veil_installer.installer_resource?{}'.format(installer_path), cwd='/opt/veil', env=env)


def mark_installed(installer_path):
    shell_execute('mv {} {}.installed'.format(installer_path, installer_path))


def shell_execute(command_line, **kwargs):
    print(green(command_line))
    command_args = shlex.split(command_line)
    try:
        process = subprocess.Popen(command_args, **kwargs)
    except:
        print(red('failed to invoke {} with {}'.format(command_args, kwargs)))
        raise
    output = process.communicate()[0]
    if process.returncode:
        raise Exception(red('shell_execute return code: {}, command: {}, kwargs: {}'.format(
            process.returncode, command_args, kwargs)))
    return output


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner

red = _wrap_with('31')
green = _wrap_with('32')

if '__main__' == __name__:
    main()