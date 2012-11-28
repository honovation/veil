from __future__ import unicode_literals, print_function, division
import sys
import os
import shlex
import subprocess
import datetime

def main():
    action = sys.argv[1]
    veil_env = sys.argv[2]
    veil_server_name = sys.argv[3]

    src_dir = '/opt/{}'.format(veil_env)
    backup_dir = '{}-backup'.format(src_dir)
    veil_server = '{}/{}'.format(veil_env, veil_server_name)
    if 'backup' == action:
        backup(src_dir, backup_dir, veil_server)
    elif 'rollback' == action:
        rollback(src_dir, backup_dir, veil_server)
    else:
        raise Exception('unknown action: {}'.format(action))


def backup(src_dir, backup_dir, veil_server):
    if not os.path.exists(src_dir):
        print('{} does not exists, skipped backup'.format(src_dir))
        return
    if os.path.exists(backup_dir):
        raise Exception('{} already exists, backup procedure abandoned')
    shell_execute('veil :{} down'.format(veil_server), cwd='{}/app'.format(src_dir))
    shell_execute('cp -r -p {} {}'.format(src_dir, backup_dir))


def rollback(src_dir, backup_dir, veil_server):
    if not os.path.exists(backup_dir):
        raise Exception('{} does not exists, can not rollback'.format(backup_dir))
    if os.path.exists(src_dir):
        shell_execute('mv {} {}-to-be-deleted-{}'.format(
            src_dir, src_dir, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')))
    shell_execute('mv {} {}'.format(backup_dir, src_dir))
    shell_execute('veil :{} up'.format(veil_server), cwd='{}/app'.format(src_dir))


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