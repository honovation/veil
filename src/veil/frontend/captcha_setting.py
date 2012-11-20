from __future__ import unicode_literals, print_function, division
from veil.backend.bucket_setting import bucket_resource
from veil.backend.redis_setting import redis_client_resource

def captcha_resources(bucket_type, bucket_base_directory, bucket_base_url, redis_host, redis_port):
    return [bucket_resource('captcha_image', bucket_type, bucket_base_directory, bucket_base_url),
            redis_client_resource('captcha_answer', host=redis_host, port=redis_port)]