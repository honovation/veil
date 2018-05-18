# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import shlex
import os
import pylxd
import pylxd.exceptions
from veil.utility.setting import *
from veil_component import as_path

LOGGER = logging.getLogger(__name__)


class LXDClient(object):
    def __init__(self, local=False, config_dir=None):
        if local:
            self.client = pylxd.Client()
        else:
            assert config_dir is not None, 'non local should provide config_dir'
            config_file = as_path(config_dir) / '.config'
            config = load_config_from(config_file, 'lxd_endpoint', 'lxd_cert_path', 'lxd_trusted_password')
            cert = (os.path.expanduser('{}/lxd.crt'.format(config.lxd_cert_path)), os.path.expanduser('{}/lxd.key'.format(config.lxd_cert_path)))
            self.client = pylxd.Client(endpoint=config.lxd_endpoint, cert=cert, verify=False, timeout=(3.05, 27))
            if not self.client.trusted:
                self.client.authenticate(config.lxd_trusted_password)
        assert self.client.trusted

    def get_container(self, name):
        return self.client.containers.get(name)

    def get_container_file_content(self, container_name, file_path):
        """
        get container file content

        :param container_name: container name
        :param file_path: file path
        :return: file content
        """
        container = self.get_container(container_name)
        LOGGER.info('Get container remote file content: %(container_name)s, %(file_path)s', {'container_name': container_name, 'file_path': file_path})
        try:
            return container.files.get(file_path)
        except pylxd.exceptions.NotFound:
            return None

    def put_container_file(self, container_name, file_path, content, mode=0644, uid=None, gid=None):
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
        container = self.get_container(container_name)
        LOGGER.info('Upload container remote file: %(container_name)s, %(file_path)s, %(mode)s, %(uid)s, %(gid)s', {
            'container_name': container_name,
            'file_path': file_path,
            'mode': mode,
            'uid': uid,
            'gid': gid
        })
        container.files.put(file_path, content, mode=mode, uid=uid, gid=gid)

    def run_container_command(self, container_name, command, env=None):
        """
        execute commands in container with env

        :param container_name: container name
        :param command: command
        :param env: environment variables
        :return:
        """
        container = self.get_container(container_name)
        LOGGER.info('Run command in container: %(container_name)s, %(command)s', {'container_name': container_name, 'command': command})
        # TODO: pylxd issue 280
        result = None
        while result is None:
            try:
                result = container.execute(shlex.split(command), environment=env or {})
            except pylxd.exceptions.NotFound:
                LOGGER.info('retry execute command in container: %(container_name)s, %(command)s', {
                    'container_name': container_name,
                    'command': command
                })
        LOGGER.info('command result: %(stdout)s, %(stderr)s, %(exit_code)s', {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.exit_code,
        })
        if result.exit_code != 0:
            raise Exception('Failed run command in container: {}, {}, {}'.format(container_name, command, result.stderr))
        return result.stdout
