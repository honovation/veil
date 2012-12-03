from __future__ import unicode_literals, print_function, division
import sys
import shlex
import os.path
import os
import subprocess


def main():
    container_name = sys.argv[1]
    sequence_no = sys.argv[2]
    user_name = sys.argv[3]
    user_password = sys.argv[4]
    installer_path = '/opt/INSTALLER-{}'.format(container_name)

    install_git()
    clone_veil()
    pull_veil()
    create_installer_file(
        installer_path=installer_path,
        container_name=container_name,
        sequence_no=sequence_no,
        user_name=user_name,
        user_password=user_password)
    install(installer_path)


def install_git():
    shell_execute('apt-get install -y git-core')


def clone_veil():
    if os.path.exists('/opt/veil'):
        return
    shell_execute('git clone git://github.com/honovation/veil.git /opt/veil')


def pull_veil():
    shell_execute('git pull', cwd='/opt/veil')


def create_installer_file(installer_path, container_name, sequence_no, user_name, user_password):
    with open(installer_path, 'w') as f:
        container_args = '&'.join([
            'container_name={}'.format(container_name),
            'sequence_no={}'.format(sequence_no),
            'user_name={}'.format(user_name),
            'user_password={}'.format(user_password)])
        iptables_rule = 'PREROUTING -p tcp -m tcp --dport {}22 -j DNAT --to-destination 10.0.3.{}:22'.format(
            sequence_no, sequence_no)
        f.write(
            """
            veil.environment.lxc.lxc_container_ready_resource?{}
            veil.environment.networking.iptables_rule_resource?table=nat&rule={}
            veil.server.os.directory_resource?path={}/.ssh
            veil.server.os.directory_resource?path=/root/.ssh
            """.format(container_args, iptables_rule, os.getenv('HOME')))
    os.chmod(installer_path, 0600)


def install(installer_path):
    shell_execute('/opt/veil/bin/veil init', cwd='/opt/veil')
    env = os.environ.copy()
#    env['VEIL_DEPENDENCY_MIRROR'] = 'http://10.0.3.254:80'
    shell_execute('veil install veil_installer.installer_resource?{}'.format(installer_path), cwd='/opt/veil', env=env)


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