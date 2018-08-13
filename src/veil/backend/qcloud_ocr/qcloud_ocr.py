# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import hmac
import logging
from base64 import b64encode
from hashlib import sha1
from random import randint

from veil.model.collection import *
from veil.utility.clock import *
from veil.utility.encoding import *
from veil.utility.http import *
from .qcloud_ocr_installer import qcloud_ocr_client_config

LOGGER = logging.getLogger(__name__)

QCLOUD_OCR_URL = 'http://recognition.image.myqcloud.com/ocr/general'


def get_request_sign(bucket_name, once_signature=False, fileid=''):
    config = qcloud_ocr_client_config()
    current_timestamp = get_current_timestamp()
    if once_signature:
        expired_time = 0
    else:
        expired_time = current_timestamp + 15 * 60
    rand = randint(0, 9999999999)
    return sign_sha1(config.appid, bucket_name, config.secret_id, config.secret_key, expired_time, current_timestamp, rand, fileid)


def sign_sha1(appid, bucket_name, secret_id, secret_key, expired_time, timestamp, rand, fileid):
    sign_data = b'a={}&b={}&k={}&e={}&t={}&r={}&u=0&f={}'.format(appid, bucket_name, secret_id, expired_time, timestamp, rand, fileid)
    sign_digest = hmac.new(to_str(secret_key), msg=sign_data, digestmod=sha1).digest()
    return b64encode(b'{}{}'.format(sign_digest, sign_data))


def get_ocr_result(bucket_name, image=None, url=None):
    if image:
        raise NotImplementedError()
    elif url:
        return get_ocr_result_by_url(bucket_name, url)
    else:
        raise NotImplementedError()


def get_ocr_result_by_url(bucket_name, url):
    config = qcloud_ocr_client_config()
    additional_header = {'Authorization': get_request_sign(bucket_name)}
    json_arguments = {'appid': config.appid, 'bucket': bucket_name, 'url': url}
    response = None
    try:
        response = requests.post(QCLOUD_OCR_URL, json=json_arguments, headers=additional_header)
        response.raise_for_status()
    except requests.HTTPError:
        LOGGER.exception('Got http error when get image ocr result by url: %(json_arguments)s, %(response)s', {
            'json_arguments': json_arguments,
            'response': response.text if response else ''
        })
        raise ImageOCRException(response.text if response else '')
    except Exception as e:
        LOGGER.exception('Got exception when get image ocr result by url: %(json_arguments)s, %(message)s, %(response)s', {
            'json_arguments': json_arguments,
            'response': response.text if response else '',
            'message': e.message
        })
        raise

    try:
        json_response = objectify(response.json())
    except Exception as e:
        LOGGER.error('Got invalid response when get image ocr result by url: %(json_arguments)s, %(response)s, %(message)s', {
            'json_arguments': json_arguments,
            'response': response.text,
            'message': e.message
        })
        raise

    LOGGER.debug('Got image ocr result successfully: %(response)s', {'response': response.text})

    if json_response.code != 0:
        LOGGER.error('Got error response when get image ocr result by url: %(json_arguments)s, %(response)s, %(message)s', {
            'json_arguments': json_arguments,
            'response': response.text,
            'message': json_response.message
        })
        raise ImageOCRException(json_response.message)
    else:
        return DictObject(line_items=json_response.data['items'])


class ImageOCRException(Exception):
    pass
