# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import gzip
import logging
import json
import socket
from time import sleep
import urllib
import urllib2
import requests
from veil.model.collection import *

LOGGER = logging.getLogger(__name__)


def http_call_use_requests(service, url, data=None, content_type=None, accept=None, accept_charset=None, accept_encoding=None, verify=False, log_data=True, log_response=True, max_tries=1, sleep_at_start=0,
        sleep_before_retry=0, http_timeout=15):
    if data:
        if content_type and content_type.startswith('application/json'):
            encoded_data = json.dumps(data)
        else:
            encoded_data = urllib.urlencode(data)
        request_method = requests.post
    else:
        request_method = requests.get
        encoded_data = None
    headers = {}
    if content_type:
        headers['Content-Type'] = content_type
    if accept:
        headers['Accept'] = accept
    if accept_charset:
        headers['Accept-Charset'] = accept_charset
    if accept_encoding:
        headers['Accept-Encoding'] = accept_encoding
    tries = 1
    if sleep_at_start > 0:
        sleep(sleep_at_start)
    while True:
        try:
            if http_timeout:
                http_response = request_method(url, headers=headers, data=encoded_data, timeout=http_timeout, verify=verify)
            else:
                http_response = request_method(url, headers=headers, data=encoded_data, verify=verify)
        except Exception as e:
            if isinstance(e, requests.exceptions.HTTPError):
                reason = 'invalid HTTP response'
            elif isinstance(e, requests.exceptions.Timeout):
                reason = 'timed out'
            elif isinstance(e, requests.exceptions.ConnectionError):
                reason = 'network problem'
            elif isinstance(e, requests.exceptions.TooManyRedirects):
                reason = 'too many redirects'
            else:
                reason = 'misc'
            if tries < max_tries:
                tries += 1
                if sleep_before_retry > 0:
                    sleep(sleep_before_retry)
            else:
                LOGGER.exception('[HTTP CALL]failed to get response: %(service)s, %(reason)s, %(url)s, %(headers)s, %(data)s, %(max_tries)s, %(timeout)s', {
                    'service': service, 'reason': reason, 'url': url, 'headers': headers, 'data': encoded_data if log_data else None,
                    'max_tries': max_tries, 'timeout': http_timeout
                })
                raise
        else:
            if 400 <= http_response.status_code < 500:  # 4xx, client error, need not retry
                LOGGER.exception('[HTTP CALL]failed to get response: %(service)s, %(reason)s, %(url)s, %(headers)s, %(data)s', {
                    'service': service, 'reason': 'cannot fulfill the request', 'url': url, 'headers': headers, 'data': encoded_data if log_data else None
                })
                raise
            response = http_response.text
            LOGGER.info('[HTTP CALL]succeeded to get response: %(service)s, %(url)s, %(headers)s, %(data)s, %(response)s', {
                'service': service, 'url': url, 'headers': headers, 'data': encoded_data if log_data else None, 'response': response if log_response else None
            })
            if accept == 'application/json':
                response = objectify(response.json())
            return response


def http_call(service, url, data=None, content_type=None, accept=None, accept_charset=None, accept_encoding=None, log_data=True, log_response=True, max_tries=1, sleep_at_start=0,
        sleep_before_retry=0, http_timeout=15):
    if data:
        if content_type and content_type.startswith('application/json'):
            encoded_data = json.dumps(data)
        else:
            encoded_data = urllib.urlencode(data)
    else:
        encoded_data = None
    request = urllib2.Request(url, data=encoded_data)
    if content_type:
        request.add_header('Content-Type', content_type)
    if accept:
        request.add_header('Accept', accept)
    if accept_charset:
        request.add_header('Accept-Charset', accept_charset)
    if accept_encoding:
        request.add_header('Accept-Encoding', accept_encoding)
    tries = 1
    if sleep_at_start > 0:
        sleep(sleep_at_start)
    while True:
        try:
            # TODO: urllib2 cannot verify server certificates, use pycurl2 instead
            if http_timeout:
                http_response = urllib2.urlopen(request, timeout=http_timeout)
            else:
                http_response = urllib2.urlopen(request)
        except Exception as e:
            if isinstance(e, urllib2.HTTPError):
                reason = 'cannot fulfill the request'
                if 400 <= e.code < 500: # 4xx, client error, need not retry
                    LOGGER.exception('[HTTP CALL]failed to get response: %(service)s, %(reason)s, %(url)s, %(headers)s, %(data)s', {
                        'service': service, 'reason': reason, 'url': url, 'headers': request.headers, 'data': request.data if log_data else None
                    })
                    raise
            elif isinstance(e, socket.timeout) or isinstance(e, urllib2.URLError) and isinstance(e.reason, socket.timeout):
                reason = 'timed out'
            elif isinstance(e, urllib2.URLError):
                reason = 'cannot reach the service'
            else:
                reason = 'misc'
            if tries < max_tries:
                tries += 1
                if sleep_before_retry > 0:
                    sleep(sleep_before_retry)
            else:
                LOGGER.exception('[HTTP CALL]failed to get response: %(service)s, %(reason)s, %(url)s, %(headers)s, %(data)s, %(max_tries)s, %(timeout)s', {
                    'service': service, 'reason': reason, 'url': url, 'headers': request.headers, 'data': request.data if log_data else None,
                    'max_tries': max_tries, 'timeout': http_timeout
                })
                raise
        else:
            if http_response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(http_response.read())
                f = gzip.GzipFile(fileobj=buf)
                response = f.read()
            else:
                response = http_response.read()
            LOGGER.info('[HTTP CALL]succeeded to get response: %(service)s, %(url)s, %(headers)s, %(data)s, %(response)s', {
                'service': service, 'url': url, 'headers': request.headers, 'data': request.data if log_data else None, 'response': response if log_response else None
            })
            if accept == 'application/json':
                response = objectify(json.loads(response))
            return response
