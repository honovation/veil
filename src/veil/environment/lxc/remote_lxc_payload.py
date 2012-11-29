from __future__ import unicode_literals, print_function, division
import sys
import shlex
import os.path
import subprocess


def main():
    container_name = sys.argv[1]
    container_ip = sys.argv[2]
    create_container(container_name)
    configure_container(container_name, container_ip)
    start_container(container_name)


def create_container(container_name):
    if os.path.exists('/var/lib/lxc/{}'.format(container_name)):
        return
    print(green('installing container {}...'.format(container_name)))
    shell_execute('lxc-create -t ubuntu -n {}'.format(container_name))


def configure_container(container_name, container_ip):
    config_path = '/var/lib/lxc/{}/config'
    with open(config_path.format(container_name)) as f:
        config = f.read()
    ip_config_line = 'lxc.network.ipv4={}'.format(container_ip)
    if 'lxc.network.ipv4' not in config:
        print(green('add {} to {}'.format(ip_config_line, config_path)))
        with open(config_path.format(container_name), 'a') as f:
            f.write('\n{}\n'.format(ip_config_line))
    else:
        if ip_config_line not in config:
            raise Exception('change ip is not supported yet')


def start_container(container_name):
    if not os.path.exists('/var/lib/lxc/{}/rootfs.hold'.format(container_name)):
        shell_execute('lxc-start -n {} -d'.format(container_name))


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