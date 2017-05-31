# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import urllib

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, ReadTimeout
from urllib3.util.retry import Retry

from veil.utility.encoding import *

requests = requests
Retry = Retry
RequestException = RequestException
ReadTimeout = ReadTimeout


def http_request(method, url, **kwargs):
    max_retries = kwargs.pop('max_retries', None)
    with requests.Session() as session:
        if max_retries:
            http_adapter = HTTPAdapter(max_retries=max_retries)
            session.mount('http://', http_adapter)
            session.mount('https://', http_adapter)
        response = session.request(method=method, url=url, **kwargs)
    return response

requests.request = http_request
requests.api.request = http_request
# TODO: remove the below two statements after requests v3 is released
hasattr(requests.Response, '__bool__') and delattr(requests.Response, '__bool__')
hasattr(requests.Response, '__nonzero__') and delattr(requests.Response, '__nonzero__')


def urlencode(query, doseq=0):
    # urllib.urlencode does not handle unicode well
    query = {to_str(k): [to_str(e) for e in v] if hasattr(v, '__iter__') else to_str(v) for k, v in query.items()}
    return urllib.urlencode(query, doseq)


def quote_plus(s, safe=b''):
    # urllib.quote_plus does not handle unicode well
    return urllib.quote_plus(to_str(s), safe)


def quote(s, safe=b'/'):
    # urllib.quote does not handle unicode well
    return urllib.quote(to_str(s), safe)


def remove_from_query_string(qs, *keys):
    if not qs or not keys:
        return qs
    key_set = set(keys)
    return '&'.join(p for p in qs.split('&') if p.split('=', 1)[0] not in key_set)
