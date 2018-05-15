# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import shlex
import os
import pylxd
import pylxd.exceptions
from veil.environment import SECURITY_CONFIG_FILE
from veil.utility.setting import *


LOGGER = logging.getLogger(__name__)


def get_lxd_client(local=False):
    if local:
        client = pylxd.Client()
    else:
        config = load_config_from(SECURITY_CONFIG_FILE, 'lxd_endpoint', 'lxd_cert_path', 'lxd_trusted_password')
        cert = (os.path.expanduser('{}/lxd.crt'.format(config.lxd_cert_path)), os.path.expanduser('{}/lxd.key'.format(config.lxd_cert_path)))
        client = pylxd.Client(endpoint=config.lxd_endpoint, cert=cert, verify=False, timeout=(3.05, 27))
        if not client.trusted:
            client.authenticate(config.lxd_trusted_password)
    assert client.trusted
    return client


def get_container_file_content(container_name, file_path):
    """
    get container file content

    :param container_name: container name
    :param file_path: file path
    :return: file content
    """
    client = get_lxd_client()
    container = client.containers.get(container_name)
    LOGGER.info('Get container remote file content: %(container_name)s, %(file_path)s', {'container_name': container_name, 'file_path': file_path})
    try:
        return container.files.get(file_path)
    except pylxd.exceptions.NotFound:
        return None


def put_container_file(container_name, file_path, content, mode=0644, uid=None, gid=None):
    """
    upload container file

    :param container_name: container name
    :param file_path: file path in container
    :param content: file content
    :param mode: file mode
    :param uid: file uid, None for root
    :param gid: file gid, None for root
    :return: None
    """
    client = get_lxd_client()
    container = client.containers.get(container_name)
    LOGGER.info('Upload container remote file: %(container_name)s, %(file_path)s, %(mode)s, %(uid)s, %(gid)s', {
        'container_name': container_name,
        'file_path': file_path,
        'mode': mode,
        'uid': uid,
        'gid': gid
    })
    container.files.put(file_path, content, mode=mode, uid=uid, gid=gid)


def run_container_command(container_name, command, env=None):
    """
    execute commands in container with env

    :param container_name: container name
    :param command: command
    :param env: environment variables
    :return:
    """
    client = get_lxd_client()
    container = client.containers.get(container_name)
    LOGGER.info('Run command on container: %(container_name)s, %(command)s', {'container_name': container_name, 'command': command})
    container.execute(shlex.split(command), environment=env or {})
