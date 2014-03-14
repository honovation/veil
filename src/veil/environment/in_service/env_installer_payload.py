from __future__ import unicode_literals, print_function, division
import sys
import os
import subprocess
import datetime


def main():
    action = sys.argv[1]
    veil_env = sys.argv[2]
    veil_server_name = sys.argv[3]

    src_dir = '/opt/{}'.format(veil_env)
    src_app_dir = '{}/app'.format(src_dir)
    backup_dir = '{}-backup'.format(src_dir)
    veil_server = '{}/{}'.format(veil_env, veil_server_name)
    if 'create-backup' == action:
        create_backup(src_dir, src_app_dir, backup_dir, veil_server)
    elif 'check-backup' == action:
        if not os.path.exists(backup_dir):
            raise Exception('backup {} does not exists'.format(backup_dir))
    elif 'delete-backup' == action:
        assert '-backup' in backup_dir
        shell_execute('rm -rf {}'.format(backup_dir))
    elif 'purge-left-overs' == action:
        purge_left_overs()
    elif 'rollback' == action:
        rollback(src_dir, backup_dir, veil_server)
    elif 'bring-down-server' == action:
        bring_down_server(src_app_dir, veil_server)
    elif 'bring-up-server' == action:
        bring_up_server(src_app_dir, veil_server)
    elif 'download-packages' == action:
        download_packages(src_app_dir, veil_server)
    elif 'upgrade-pip' == action:
        setuptools_version = sys.argv[4]
        pip_version = sys.argv[5]
        upgrade_pip(src_app_dir, veil_server, setuptools_version, pip_version)
    else:
        raise Exception('unknown action: {}'.format(action))


def create_backup(src_dir, src_app_dir, backup_dir, veil_server):
    if not os.path.exists(src_app_dir):
        print('{}/app does not exists, skipped backup'.format(src_dir))
        return
    if os.path.exists(backup_dir):
        raise Exception('{} already exists, backup procedure abandoned'.format(backup_dir))
    bring_down_server(src_dir, veil_server)
    shell_execute('cp -r -p {} {}'.format(src_dir, backup_dir))
    shell_execute('git reset --hard HEAD', cwd=src_app_dir)


def rollback(src_dir, backup_dir, veil_server):
    if not os.path.exists(backup_dir):
        raise Exception('{} does not exists, can not rollback'.format(backup_dir))
    if os.path.exists(src_dir):
        bring_down_server(src_dir, veil_server)
        shell_execute('mv {} {}-to-be-deleted-{}'.format(src_dir, src_dir, datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    try:
        shell_execute('pkill -x supervisord')
    except:
        pass  # do not care if it is there
    shell_execute('cp -r -p {} {}'.format(backup_dir, src_dir))


def bring_down_server(src_app_dir, veil_server):
    shell_execute('veil :{} down'.format(veil_server), cwd=src_app_dir)


def bring_up_server(src_app_dir, veil_server):
    shell_execute('veil :{} up --daemonize'.format(veil_server), cwd=src_app_dir)


def upgrade_pip(src_app_dir, veil_server, setuptools_version, pip_version):
    shell_execute('veil :{} upgrade-pip {} {}'.format(veil_server, setuptools_version, pip_version), cwd=src_app_dir)


def purge_left_overs():
    for name in os.listdir('/opt'):
        if 'to-be-deleted' in name or name.endswith('-backup'):
            shell_execute('rm -rf {}'.format('/opt/{}'.format(name)))


def download_packages(src_app_dir, veil_server):
    if not os.path.exists(src_app_dir):
        print('{} does not exists, skipped download'.format(src_app_dir))
        return
    shell_execute('git archive --format=tar --remote=origin master RESOURCE-LATEST-VERSION RESOURCE-LATEST-VERSION-TEST | tar -x', cwd=src_app_dir)
    try:
        shell_execute('veil :{} install-server --download-only'.format(veil_server), cwd=src_app_dir)
    finally:
        shell_execute('git checkout -- RESOURCE-LATEST-VERSION RESOURCE-LATEST-VERSION-TEST', cwd=src_app_dir)


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