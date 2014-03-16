from __future__ import unicode_literals, print_function, division
import subprocess
import sys
import os


def main():
    veil_framework_codebase = sys.argv[1]
    application_codebase = sys.argv[2]
    veil_env_name = sys.argv[3]
    veil_server_name = sys.argv[4]
    action = sys.argv[5]
    veil_home = '/opt/{}/app'.format(veil_env_name)
    veil_framework_home = '/opt/{}/veil'.format(veil_env_name)
    application_branch = 'env-{}'.format(veil_env_name)

    if action not in ('DEPLOY', 'PATCH'):
        raise Exception('unknown action: {}'.format(action))

    disable_time_sync()
    install_git()
    clone_application(application_codebase, veil_home)
    pull_application(application_branch, veil_home)
    framework_version = read_framework_version(veil_home)
    clone_veil(veil_framework_codebase, veil_framework_home)
    pull_veil(framework_version, veil_framework_home)

    if 'DEPLOY' == action:
        deploy(veil_framework_home, veil_home, veil_env_name, veil_server_name)
    else:  # PATCH
        patch(veil_framework_home, veil_home, veil_env_name, veil_server_name)


def disable_time_sync():
    """disable time sync on lxc guests"""
    shell_execute('apt-get -y remove ntpdate ntp')


def install_git():
    shell_execute('service resolvconf restart')
    shell_execute('apt-get -y install git-core')


def clone_application(application_codebase, veil_home):
    if os.path.exists(veil_home):
        return
    shell_execute('git clone {} {}'.format(application_codebase, veil_home))


def pull_application(application_branch, veil_home):
    shell_execute('git checkout {}'.format(application_branch), cwd=veil_home)
    while True:
        try:
            shell_execute('git pull --rebase', cwd=veil_home)
        except:
            continue
        else:
            break


def read_framework_version(veil_home):
    framework_version = 'master'
    framework_version_file = os.path.join(veil_home, 'VEIL-VERSION')
    if os.path.exists(framework_version_file):
        with open(framework_version_file) as f:
            framework_version = f.read()
    return framework_version


def clone_veil(veil_framework_codebase, veil_framework_home):
    if os.path.exists(veil_framework_home):
        return
    shell_execute('git clone {} {}'.format(veil_framework_codebase, veil_framework_home))


def pull_veil(framework_version, veil_framework_home):
    shell_execute('git checkout {}'.format(framework_version), cwd=veil_framework_home)
    while True:
        try:
            shell_execute('git pull --rebase', cwd=veil_framework_home)
        except:
            continue
        else:
            break


def deploy(veil_framework_home, veil_home, veil_env_name, veil_server_name):
    env = os.environ.copy()
    shell_execute('{}/bin/veil :{}/{} deploy'.format(veil_framework_home, veil_env_name, veil_server_name),
        cwd=veil_home, env=env)


def patch(veil_framework_home, veil_home, veil_env_name, veil_server_name):
    env = os.environ.copy()
    shell_execute('{}/bin/veil :{}/{} patch'.format(veil_framework_home, veil_env_name, veil_server_name),
        cwd=veil_home, env=env)


def shell_execute(command_line, **kwargs):
    print(green(command_line))
    try:
        process = subprocess.Popen(command_line, shell=True, **kwargs)
    except:
        print(red('failed to invoke {} with {}'.format(command_line, kwargs)))
        raise
    output = process.communicate()[0]
    if process.returncode:
        print(red('Subprocess return code: {}, command_line: {}, kwargs: {}, output: {}'.format(process.returncode,
            command_line, kwargs, output)))
        raise Exception(red('shell_execute return code: {}, command_line: {}, kwargs: {}'.format(process.returncode,
            command_line, kwargs)))
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