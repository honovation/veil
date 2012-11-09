import subprocess
import shlex
import os.path
import sys
import os

def main():
    application_codebase = sys.argv[1]
    veil_home = sys.argv[2]
    veil_env = sys.argv[3]
    veil_server_name = sys.argv[4]
    install_git()
    clone_application(application_codebase, veil_home)
    pull_application(veil_home, veil_env)
    veil_version = read_veil_version(veil_home)
    clone_veil()
    pull_veil(veil_version)
    deploy(veil_home, veil_env, veil_server_name)


def install_git():
    shell_execute('apt-get install -y git-core')


def clone_application(application_codebase, veil_home):
    if os.path.exists(veil_home):
        return
    shell_execute('git clone {} {}'.format(application_codebase, veil_home))


def pull_application(veil_home, veil_env):
    shell_execute('git checkout env-{}'.format(veil_env), cwd=veil_home)
    shell_execute('git pull', cwd=veil_home)


def read_veil_version(veil_home):
    veil_version = 'master'
    veil_version_file = os.path.join(veil_home, 'VEIL-VERSION')
    if os.path.exists(veil_version_file):
        with open(veil_version_file) as f:
            veil_version = f.read()
    return veil_version


def clone_veil():
    if os.path.exists('/opt/veil'):
        return
    shell_execute('git clone git://github.com/honovation/veil.git /opt/veil')


def pull_veil(veil_version):
    shell_execute('git checkout {}'.format(veil_version), cwd='/opt/veil')
    shell_execute('git pull', cwd='/opt/veil')


def deploy(veil_home, veil_env, veil_server_name):
    env = os.environ.copy()
    env['VEIL_DEPENDENCY_MIRROR'] = 'http://200.200.200.25:8080'
    shell_execute('/opt/veil/bin/veil :{}/{} deploy'.format(veil_env, veil_server_name), cwd=veil_home, env=env)


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