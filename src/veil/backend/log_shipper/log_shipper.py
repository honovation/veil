from __future__ import unicode_literals, print_function, division
import redis.client
import time
import os
import logging
from veil.frontend.cli import *
from veil.utility.shell import *
from .log_shipper_installer import load_log_shipper_config

# Written according to https://github.com/josegonzalez/beaver/blob/master/beaver/worker.py

LOGGER = logging.getLogger(__name__)

@script('up')
def bring_up_log_shipper():
    shippers = []
    for log_path, redis_config in load_log_shipper_config().items():
        redis_client = redis.client.StrictRedis(host=redis_config.host, port=redis_config.port)
        shippers.append(LogShipper(log_path, redis_client, redis_config.key))
    while True:
        for shipper in shippers:
            shipper.ship()
        time.sleep(0.1)


class LogShipper(object):
    def __init__(self, log_path, redis_client, redis_key):
        super(LogShipper, self).__init__()
        self.log_path = log_path
        self.redis_client = redis_client
        self.redis_key = redis_key
        self.open_log_file()

    def ship(self):
        if self.log_file:
            lines = self.log_file.readlines()
            for line in lines:
                self.redis_client.rpush(self.redis_key, line.strip())
        self.open_latest_log_file()

    def open_latest_log_file(self):
        # log path might point to different file due to log rotation
        if self.log_file:
            latest_log_file_id = load_file_id(self.log_path)
            if latest_log_file_id != self.log_file_id:
                self.log_file_id = latest_log_file_id
                self.log_file = open(self.log_path, 'r')
                LOGGER.info('reopened latest log file: %(path)s => %(file_id)s', {
                    'path': self.log_path,
                    'file_id': self.log_file_id
                })
        else:
            self.open_log_file()

    def open_log_file(self):
        if os.path.exists(self.log_path):
            self.log_file_id = load_file_id(self.log_path)
            self.log_file = open(self.log_path, 'r')
            LOGGER.info('opened log file: %(path)s => %(file_id)s', {
                'path': self.log_path,
                'file_id': self.log_file_id
            })
            self.log_file.seek(os.path.getsize(self.log_file.name)) # skip old logs, assuming we started before them
        else:
            self.log_file_id = None
            self.log_file = None


def load_file_id(path):
    if os.path.exists(path):
        st = os.stat(path)
        return st.st_dev, st.st_ino
    else:
        return None
