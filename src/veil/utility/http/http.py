# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import urllib

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, ReadTimeout
from requests.packages.urllib3 import Retry

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


def urlencode(params, doseq=0):
    # urllib.urlencode does not handle unicode well
    params = {to_str(k): to_str(v) for k, v in params.items()}
    return urllib.urlencode(params, doseq)
