from __future__ import unicode_literals, print_function, division
import sys
import shlex
import os.path
import os
import subprocess


def main():
    installer_path = sys.argv[1]

    enable_time_sync()
    install_git()
    clone_veil()
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


def clone_veil():
    if os.path.exists('/opt/veil'):
        return
    shell_execute('git clone git://github.com/honovation/veil.git /opt/veil')


def pull_veil():
    while True:
        try:
            shell_execute('git pull', cwd='/opt/veil')
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
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner

red = _wrap_with('31')
green = _wrap_with('32')

if '__main__' == __name__:
    main()