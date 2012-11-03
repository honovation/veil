from __future__ import unicode_literals, print_function, division
from veil.backend.bucket import *
from veil.backend.redis import *
from veil.environment.setting import *

def captcha_settings(website, redis_port):
    return merge_settings(
        bucket_settings('captcha_image', website),
        redis_settings('captcha_answer', port=6389))