# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import contextlib
from datetime import timedelta
import functools
import logging
import uuid
from veil.backend.job_queue import *
from veil.utility.pillow import *
from veil.utility.shell import *
from veil.frontend.template import *
from veil.frontend.web import *
from veil.backend.bucket import *
from veil.backend.redis import *
from veil.environment import *

LOGGER = logging.getLogger(__name__)
bucket = register_bucket('captcha_image')
redis = register_redis('persist_store')

CAPTCHA_ANSWER_ALIVE_MINUTES = 10
CAPTCHA_ANSWER_ALIVE_TIME = timedelta(minutes=CAPTCHA_ANSWER_ALIVE_MINUTES)


def register_captcha(website):
    import_widget(captcha_widget)
    route('GET', '/captcha', website=website, tags=(TAG_NO_LOGIN_REQUIRED,))(captcha_widget)
    route('GET', '/captcha.json', website=website, tags=(TAG_NO_LOGIN_REQUIRED,))(get_captcha_json)
    return captcha_protected


@widget
def captcha_widget():
    challenge_code, captcha_image_url = generate_captcha()
    return get_template('captcha.html').render(challenge_code=challenge_code, captcha_image_url=captcha_image_url)


def get_captcha_json():
    challenge_code, captcha_image_url = generate_captcha()
    return dict(challenge_code=challenge_code, captcha_image_url=captcha_image_url)


def generate_captcha():
    challenge_code = uuid.uuid4().get_hex()
    image, answer = generate_captcha_image_and_answer(size=(150, 30), font_size=25, draw_lines=True, draw_points=True)
    redis().setex(captcha_redis_key(challenge_code), CAPTCHA_ANSWER_ALIVE_TIME, answer)
    bucket_key = captcha_bucket_key(challenge_code)
    with contextlib.closing(StringIO()) as buffer_:
        image.save(buffer_, 'GIF', transparency=0)
        buffer_.reset()
        bucket().store(bucket_key, buffer_)
    return challenge_code, bucket().get_url(bucket_key)


def validate_captcha():
    challenge_code = get_http_argument('captcha_challenge_code', optional=True)
    delete_http_argument('captcha_challenge_code')
    captcha_answer = get_http_argument('captcha_answer', optional=True)
    delete_http_argument('captcha_answer')
    return validate(challenge_code, captcha_answer)


def captcha_protected(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['captcha_errors'] = validate_captcha()
        return func(*args, **kwargs)

    return wrapper


def validate(challenge_code, captcha_answer):
    request = get_current_http_request()
    real_answer = redis().get(captcha_redis_key(challenge_code))
    if VEIL_ENV.is_test or (captcha_answer and real_answer == captcha_answer):
        if not VEIL_ENV.is_test:
            LOGGER.info('[sensitive]validate captcha succeeded: %(site)s, %(function)s, %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'site': request.host,
                'function': 'captcha',
                'uri': request.uri,
                'referer': request.referrer.raw,
                'remote_ip': request.remote_ip,
                'user_agent': request.user_agent.ua_string
            })
        return {}
    else:
        LOGGER.warn('[sensitive]validate captcha failed: %(site)s, %(function)s, %(user_answer)s, %(real_answer)s, %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
            'site': request.host,
            'function': 'captcha',
            'user_answer': captcha_answer,
            'real_answer': real_answer,
            'uri': request.uri,
            'referer': request.referrer.raw,
            'remote_ip': request.remote_ip,
            'user_agent': request.user_agent.ua_string
        })
        return {'captcha_answer': ['验证码{}，请重新填入正确的计算结果'.format('错误' if real_answer else '过期')]}


def captcha_redis_key(challenge_code):
    return 'CAPTCHA:{}'.format(challenge_code)


def captcha_bucket_key(challenge_code):
    return '{}/{}.gif'.format(challenge_code[:2], challenge_code[2:])


@task(queue='clean_up_captcha_images', schedule=cron_expr('11 * * * *'))
def clean_up_captcha_images():
    if not isinstance(bucket(), FilesystemBucket):
        LOGGER.warn('failed as captcha images are not saved in file-system-based bucket')
        return
    if not bucket().base_directory.exists():
        return
    try:
        shell_execute('find {} -type f -mmin +{} -delete'.format(bucket().base_directory, CAPTCHA_ANSWER_ALIVE_MINUTES * 2), capture=True)
    except Exception as e:
        LOGGER.info('clean up captcha images got exception: %(message)s', {'message': e.message})
