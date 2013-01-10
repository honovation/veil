from __future__ import unicode_literals, print_function, division
import redis.client
import time
import datetime
import os
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *
from .log_shipper_installer import load_log_shipper_config
from .log_shipper_installer import VEIL_LOG_ARCHIVE_DIR

@script('up')
def bring_up_log_shipper():
    archive_old_logs()
    shippers = []
    for log_path, redis_config in load_log_shipper_config().items():
        redis_client = redis.client.StrictRedis(host=redis_config.host, port=redis_config.port)
        shippers.append(LogShipper(log_path, redis_client, redis_config.key))
    while True:
        for shipper in shippers:
            shipper.ship()
        time.sleep(0.1)


def archive_old_logs():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    shell_execute('tar -pczf {} {}'.format(VEIL_LOG_ARCHIVE_DIR / '{}.tar.gz'.format(timestamp), VEIL_LOG_DIR))
    for root, dirs, files in os.walk(VEIL_LOG_DIR): # remove files keep dirs
        for file in files:
            os.remove(os.path.join(root, file))


class LogShipper(object):
    def __init__(self, log_path, redis_client, redis_key):
        super(LogShipper, self).__init__()
        self.log_path = log_path
        self.redis_client = redis_client
        self.redis_key = redis_key
        self.open_log_file()

    def ship(self):
        self.open_latest_log_file()
        if self.log_file:
            lines = self.log_file.readlines()
            for line in lines:
                self.redis_client.rpush(self.redis_key, line.strip())

    def open_latest_log_file(self):
        # log path might point to different file due to log rotation
        if self.log_file:
            latest_log_file_id = load_file_id(self.log_path)
            if latest_log_file_id != self.log_file_id:
                self.log_file_id = latest_log_file_id
                self.log_file = open(self.log_path, 'r')
        else:
            self.open_log_file()

    def open_log_file(self):
        if os.path.exists(self.log_path):
            self.log_file_id = load_file_id(self.log_path)
            self.log_file = open(self.log_path, 'r')
        else:
            self.log_file_id = None
            self.log_file = None


def load_file_id(path):
    st = os.stat(path)
    return st.st_dev, st.st_ino
