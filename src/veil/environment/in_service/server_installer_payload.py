from __future__ import unicode_literals, print_function, division
import subprocess
import shlex
import os.path
import sys
import os

def main():
    application_codebase = sys.argv[1]
    veil_env = sys.argv[2]
    veil_server_name = sys.argv[3]
    veil_home = '/opt/{}/app'.format(veil_env)
    veil_framework_home = '/opt/{}/veil'.format(veil_env)
    application_branch = 'env-{}'.format(veil_env)

    install_git()
    clone_application(application_codebase, veil_home)
    pull_application(application_branch, veil_home)
    framework_version = read_framework_version(veil_home)
    clone_veil(veil_framework_home)
    pull_veil(framework_version, veil_framework_home)
    deploy(veil_framework_home, veil_home, veil_env, veil_server_name)


def install_git():
    #shell_execute('apt-get update')
    shell_execute('apt-get install -y git-core')


def clone_application(application_codebase, veil_home):
    if os.path.exists(veil_home):
        return
    shell_execute('git clone {} {}'.format(application_codebase, veil_home))


def pull_application(application_branch, veil_home):
    shell_execute('git checkout {}'.format(application_branch), cwd=veil_home)
    while True:
        try:
            shell_execute('git pull', cwd=veil_home)
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


def clone_veil(veil_framework_home):
    if os.path.exists(veil_framework_home):
        return
    shell_execute('git clone git://github.com/honovation/veil.git {}'.format(veil_framework_home))


def pull_veil(framework_version, veil_framework_home):
    shell_execute('git checkout {}'.format(framework_version), cwd=veil_framework_home)
    while True:
        try:
            shell_execute('git pull', cwd=veil_framework_home)
        except:
            continue
        else:
            break


def deploy(veil_framework_home, veil_home, veil_env, veil_server_name):
    env = os.environ.copy()
    shell_execute('{}/bin/veil :{}/{} deploy'.format(
        veil_framework_home, veil_env, veil_server_name), cwd=veil_home, env=env)


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