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
        shippers.append(LogShipper(log_path, open(log_path, 'r'), redis_client, redis_config.key))
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
    def __init__(self, log_path, log_file, redis_client, redis_key):
        super(LogShipper, self).__init__()
        self.log_path = log_path
        self.log_file = log_file
        self.redis_client = redis_client
        self.redis_key = redis_key

    def ship(self):
        lines = self.log_file.readlines()
        for line in lines:
            self.redis_client.rpush(self.redis_key, line.strip())