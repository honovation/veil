from __future__ import unicode_literals, print_function, division
from veil.backend.bucket_setting import bucket_settings
from veil.backend.redis_setting import redis_settings
from veil.environment.setting import *

def captcha_settings(website, redis_port):
    return merge_settings(
        bucket_settings('captcha_image', website),
        redis_settings('captcha_answer', port=6389))