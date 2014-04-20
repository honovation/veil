from __future__ import unicode_literals, print_function, division
import sys
import os
import subprocess


def main():
    veil_framework_codebase = sys.argv[1]
    installer_path = sys.argv[2]

    enable_time_sync()
    install_git()
    clone_veil(veil_framework_codebase)
    pull_veil()
    install(installer_path)
    mark_installed(installer_path)


def enable_time_sync():
    """enable time sync on lxc hosts, and which is shared among lxc guests"""
    shell_execute('apt-get -y install ntpdate')
    if os.path.exists('/etc/cron.hourly/ntpdate'):
        return
    unsafe_call('''printf '#!/bin/sh\n/usr/sbin/ntpdate ntp.ubuntu.com time.nist.gov' > /etc/cron.hourly/ntpdate && chmod 755 /etc/cron.hourly/ntpdate''')


def install_git():
    shell_execute('apt-get -y install git-core')


def clone_veil(veil_framework_codebase):
    if os.path.exists('/opt/veil'):
        return
    shell_execute('git clone {} /opt/veil'.format(veil_framework_codebase))


def pull_veil():
    while True:
        try:
            shell_execute('git pull --rebase', cwd='/opt/veil')
        except:
            continue
        else:
            break


def install(installer_path):
    shell_execute('/opt/veil/bin/veil init', cwd='/opt/veil')
    env = os.environ.copy()
    shell_execute('veil install veil_installer.installer_resource?{}'.format(installer_path), cwd='/opt/veil', env=env)


def mark_installed(installer_path):
    shell_execute('mv {} {}.installed'.format(installer_path, installer_path))


def shell_execute(command_line, **kwargs):
    print(green(command_line))
    try:
        process = subprocess.Popen(command_line, shell=True, **kwargs)
    except:
        print(red('failed to invoke {} with {}'.format(command_line, kwargs)))
        raise
    output = process.communicate()[0]
    if process.returncode:
        print(red('Subprocess return code: {}, command_line: {}, kwargs: {}, output: {}'.format(process.returncode, command_line, kwargs, output)))
        raise Exception(red('shell_execute return code: {}, command_line: {}, kwargs: {}'.format(process.returncode, command_line, kwargs)))
    return output


def unsafe_call(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output = process.communicate()[0]
    if process.returncode:
        raise Exception('failed to execute: {}'.format(command))
    return output


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = '1;{}'.format(c)
        return '\033[{}m{}\033[0m'.format(c, text)

    return inner

red = _wrap_with('31')
green = _wrap_with('32')

if '__main__' == __name__:
    main()