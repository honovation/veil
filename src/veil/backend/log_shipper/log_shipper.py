from __future__ import unicode_literals, print_function, division
import time
import os
import logging
from veil.environment import VEIL_ENV_TYPE
from redis.client import StrictRedis
from veil.frontend.cli import *
from veil.model.event import event
from veil.server.process import EVENT_PROCESS_TEARDOWN
from .log_shipper_installer import load_log_shipper_config

# Written according to https://github.com/josegonzalez/beaver/blob/master/beaver/worker.py

LOGGER = logging.getLogger(__name__)

shippers = []


@script('up')
def bring_up_log_shipper():
    for log_path, redis_config in load_log_shipper_config().items():
        redis_client = StrictRedis(host=redis_config.host, port=redis_config.port)
        shippers.append(LogShipper(log_path, redis_client, redis_config.key))
    while True:
        for shipper in shippers:
            try:
                shipper.ship()
            except Exception:
                LOGGER.exception('failed to ship log: %(path)s', {'path': shipper.log_path})
        time.sleep(0.1)


@event(EVENT_PROCESS_TEARDOWN)
def close_shipper_log_files():
    for shipper in shippers:
        if 'test' != VEIL_ENV_TYPE:
            LOGGER.debug('close shipper log file at exit: %(path)s', {'path': shipper.log_path})
        shipper.close_log_file()


class LogShipper(object):
    def __init__(self, log_path, redis_client, redis_key):
        super(LogShipper, self).__init__()
        self.log_path = log_path
        self.redis_client = redis_client
        self.redis_key = redis_key
        self.log_file_id = None
        self.log_file = None
        self.open_log_file()  # open the log file as soon as possible

    def ship(self):
        if not self.log_file:
            self.open_log_file()
        if self.log_file:
            cur_pos, eof_pos_at_start_time = get_file_current_and_eof_positions(self.log_file)
            for line in iter(self.log_file.readline, ''):  # do not use "for line in self.log_file" due to its read-ahead behavior
                line = line.strip()
                if line:
                    try:
                        self.redis_client.rpush(self.redis_key, line)
                    except Exception:
                        LOGGER.exception('failed to push log: %(line)s, %(path)s', {'line': line, 'path': self.log_path})
                        self.wait_for_redis_back()
                        try:
                            self.redis_client.rpush(self.redis_key, line)
                        except Exception:
                            LOGGER.critical('failed to push log again: %(line)s, %(path)s', {'line': line, 'path': self.log_path}, exc_info=1)
                            self.log_file.seek(cur_pos)
                            break
                cur_pos = self.log_file.tell()
                if cur_pos >= eof_pos_at_start_time:  # avoid the current shipper keeps shipping and other shippers get no chance
                    break
            self.open_latest_log_file()

    def open_latest_log_file(self):
        # log path might point to different file due to log rotation
        cur_pos, eof_pos = get_file_current_and_eof_positions(self.log_file)
        if cur_pos < eof_pos:
            return
        latest_log_file_id = load_file_id(self.log_path)
        if latest_log_file_id and latest_log_file_id != self.log_file_id:
            latest_log_file = open(self.log_path, 'r')
            self.close_log_file()
            self.log_file_id = latest_log_file_id
            self.log_file = latest_log_file
            LOGGER.info('reopened latest log file: %(path)s => %(file_id)s', {'path': self.log_path, 'file_id': self.log_file_id})

    def open_log_file(self):
        if os.path.exists(self.log_path):
            try:
                self.log_file_id = load_file_id(self.log_path)
                self.log_file = open(self.log_path, 'r')
                # TODO: [enhancement] remember the latest file position (file_id, latest_pos) to avoid losing logs when restarting log shipper
                self.log_file.seek(0, os.SEEK_END)
            except Exception:
                LOGGER.critical('failed to open log file: %(path)s', {'path': self.log_path}, exc_info=1)
                self.close_log_file()
                self.log_file_id = None
                self.log_file = None
            else:
                LOGGER.info('opened log file: %(path)s => %(file_id)s', {'path': self.log_path, 'file_id': self.log_file_id})
        else:
            LOGGER.warn('log file not found or no permission to access: %(path)s', {'path': self.log_path})
            self.log_file_id = None
            self.log_file = None

    def close_log_file(self):
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.close()
            except Exception:
                LOGGER.warn('Cannot close log file: %(path)s', {'path': self.log_path}, exc_info=1)

    def wait_for_redis_back(self):
        while True:
            time.sleep(1)
            try:
                self.redis_client.llen(self.redis_key)
            except Exception:
                LOGGER.exception('log collector still unavailable')
            else:
                LOGGER.info('log collector back to available now')
                return

    def __repr__(self):
        return 'Shipper with log_path <{}> and redis_key <{}>'.format(self.log_path, self.redis_key)


def load_file_id(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    return st.st_dev, st.st_ino


def get_file_current_and_eof_positions(f):
    cur_pos = f.tell()
    f.seek(0, os.SEEK_END)
    eof_pos = f.tell()
    f.seek(cur_pos)
    return cur_pos, eof_pos
