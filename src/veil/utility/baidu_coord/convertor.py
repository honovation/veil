# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from decimal import Decimal
from math import sqrt, pow, sin, cos, atan2

import lxml.objectify
from veil.model.collection import *
from veil.utility.http import *


API_URL = 'http://api.map.baidu.com/geoconv/v1/'
COORDS_COUNT_LIMIT = 100
JSON_OUTPUT = 'json'
XML_OUTPUT = 'xml'
X_PI = Decimal('3.14159265358979324') * Decimal('3000.0') / Decimal('180.0')

LOGGER = logging.getLogger(__name__)


def convert_to_baidu_coord(coords, ak, sn=None, from_type=1, to_type=5, output=JSON_OUTPUT):
    if len(coords) > COORDS_COUNT_LIMIT:
        raise Exception('coords too much: limit is {}'.format(COORDS_COUNT_LIMIT))
    params = DictObject(coords=[';'.join(','.join(coord) for coord in coords)], ak=ak, sn=sn, to=to_type, output=output)
    params['from'] = from_type

    response = None
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
    except Exception:
        LOGGER.info('got exception when call convert to baidu coord: %(params)s, %(result)s', {
            'params': params,
            'result': response.content if response is not None else ''
        })
    else:
        if output == JSON_OUTPUT:
            parsed_output = objectify(response.json())
        else:
            parsed_output = DictObject()
            root = lxml.objectify.fromstring(response)
            for e in root.iterchildren():
                if e.text:
                    parsed_output[e.tag] = e.text
        if parsed_output.status != 0:
            raise Exception('invalid output status when call convert to baidu coord: {}'.format(response.content))
        return parsed_output.result


def convert_baidu_coord_to_cgj02(coords):
    decrypted_coords = []
    for coord in coords:
        bd_lon = coord[0]
        bd_lat = coord[1]
        x = bd_lon - Decimal('0.0065')
        y = bd_lat - Decimal('0.006')
        z = Decimal(sqrt(pow(x, 2) + pow(y, 2))) - Decimal('0.00002') * Decimal(sin(y * X_PI))
        theta = Decimal(atan2(y, x)) - Decimal('0.000003') * Decimal(cos(x * X_PI))
        decrypted_coords.append((Decimal(z * Decimal(cos(theta))), Decimal(z * Decimal(sin(theta)))))
    return decrypted_coords
