import subprocess
import shlex
import os.path
import sys

def main():
    application_codebase = sys.argv[1]
    veil_home = sys.argv[2]
    veil_env = sys.argv[3]
    veil_server_name = sys.argv[4]
    install_packages()
    clone_veil()
    pull_veil()
    clone_application(application_codebase, veil_home)
    pull_application(veil_home, veil_env)
    deploy(veil_home, veil_env, veil_server_name)


def install_packages():
    #shell_execute('apt-get update')
    # language-pack-en unzip, wget is not provided by lxc container
    # before we have server provisioning script, we put those dependency here
    shell_execute('apt-get install -y git-core language-pack-en unzip wget')

def clone_veil():
    if os.path.exists('/opt/veil'):
        return
    shell_execute('git clone git://github.com/honovation/veil.git /opt/veil')


def pull_veil():
    shell_execute('git pull', cwd='/opt/veil')


def clone_application(application_codebase, veil_home):
    if os.path.exists(veil_home):
        return
    shell_execute('git clone {} {}'.format(application_codebase, veil_home))


def pull_application(veil_home, veil_env):
    shell_execute('git checkout env-{}'.format(veil_env), cwd=veil_home)
    shell_execute('git pull', cwd=veil_home)


def deploy(veil_home, veil_env, veil_server_name):
    print(green('backup old version var dir'))
    shell_execute('veil :{}/{} ljmall backup deploy_backup'.format(veil_env, veil_server_name), cwd=veil_home)
    shell_execute('/opt/veil/bin/veil init', cwd=veil_home)
    shell_execute('veil :{}/{} environment deployment install'.format(veil_env, veil_server_name), cwd=veil_home)
    shell_execute('veil :{}/{} deploy'.format(veil_env, veil_server_name), cwd=veil_home)


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