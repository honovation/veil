from __future__ import unicode_literals, print_function, division
import time
from veil.frontend.cli import *
from veil.backend.redis import *

redis = register_redis('log_collector')

@script('up')
def bring_up_log_shipper(log_file_path, redis_key):
    with open(log_file_path, 'r') as file:
        while True:
            lines = file.readlines()
            for line in lines:
                redis().rpush(redis_key, line)
            time.sleep(0.1)