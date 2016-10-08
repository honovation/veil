# -*- coding: utf-8 -*-
"""
References:
    https://github.com/googollee/eviltransform
    https://github.com/wandergis/coordtransform
"""
from __future__ import unicode_literals, print_function, division
import math

from decimal import Decimal

EARTH_RADIUS = 6378137.0


def out_of_china(lng, lat):
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def transform(lng, lat):
    lng_x_lat = lng * lat
    sqrt_abs_lng = math.sqrt(abs(lng))
    lng_x_pi = lng * math.pi
    lat_x_pi = lat * math.pi

    new_lng = new_lat = 20.0 * math.sin(6.0 * lng_x_pi) + 20.0 * math.sin(2.0 * lng_x_pi)

    new_lng += 20.0 * math.sin(lng_x_pi) + 40.0 * math.sin(lng_x_pi / 3.0)
    new_lat += 20.0 * math.sin(lat_x_pi) + 40.0 * math.sin(lat_x_pi / 3.0)

    new_lng += 150.0 * math.sin(lng_x_pi / 12.0) + 300.0 * math.sin(lng_x_pi / 30.0)
    new_lat += 160.0 * math.sin(lat_x_pi / 12.0) + 320 * math.sin(lat_x_pi / 30.0)

    new_lng *= 2.0 / 3.0
    new_lat *= 2.0 / 3.0

    new_lng += 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng_x_lat + 0.1 * sqrt_abs_lng
    new_lat += -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng_x_lat + 0.2 * sqrt_abs_lng

    return new_lng, new_lat


def delta(lng, lat):
    ee = 0.00669342162296594323
    d_lng, d_lat = transform(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lng = (d_lng * 180.0) / (EARTH_RADIUS / sqrt_magic * math.cos(rad_lat) * math.pi)
    d_lat = (d_lat * 180.0) / ((EARTH_RADIUS * (1 - ee)) / (magic * sqrt_magic) * math.pi)
    return d_lng, d_lat


def wgs2gcj(wgs_lng, wgs_lat):
    if isinstance(wgs_lng, Decimal):
        gcj_lng, gcj_lat = _wgs2gcj(float(wgs_lng), float(wgs_lat))
        gcj_lng = Decimal(gcj_lng)
        gcj_lat = Decimal(gcj_lat)
    else:
        gcj_lng, gcj_lat = _wgs2gcj(wgs_lng, wgs_lat)
    return gcj_lng, gcj_lat


def _wgs2gcj(wgs_lng, wgs_lat):
    if out_of_china(wgs_lng, wgs_lat):
        return wgs_lng, wgs_lat
    else:
        d_lng, d_lat = delta(wgs_lng, wgs_lat)
        return wgs_lng + d_lng, wgs_lat + d_lat


def gcj2wgs(gcj_lng, gcj_lat):
    if isinstance(gcj_lng, Decimal):
        wgs_lng, wgs_lat = _gcj2wgs(float(gcj_lng), float(gcj_lat))
        wgs_lng = Decimal(wgs_lng)
        wgs_lat = Decimal(wgs_lat)
    else:
        wgs_lng, wgs_lat = _gcj2wgs(gcj_lng, gcj_lat)
    return wgs_lng, wgs_lat


def _gcj2wgs(gcj_lng, gcj_lat):
    if out_of_china(gcj_lng, gcj_lat):
        return gcj_lng, gcj_lat
    else:
        d_lng, d_lat = delta(gcj_lng, gcj_lat)
        return gcj_lng - d_lng, gcj_lat - d_lat


def gcj2wgs_exact(gcj_lng, gcj_lat):
    if isinstance(gcj_lng, Decimal):
        wgs_lng, wgs_lat = _gcj2wgs_exact(float(gcj_lng), float(gcj_lat))
        wgs_lng = Decimal(wgs_lng)
        wgs_lat = Decimal(wgs_lat)
    else:
        wgs_lng, wgs_lat = _gcj2wgs_exact(gcj_lng, gcj_lat)
    return wgs_lng, wgs_lat


def _gcj2wgs_exact(gcj_lng, gcj_lat):
    init_delta = 0.01
    threshold = 0.000001
    d_lat = d_lng = init_delta
    m_lng = gcj_lng - d_lng
    m_lat = gcj_lat - d_lat
    p_lng = gcj_lng + d_lng
    p_lat = gcj_lat + d_lat
    for i in range(30):
        wgs_lng = (m_lng + p_lng) / 2
        wgs_lat = (m_lat + p_lat) / 2
        tmp_lng, tmp_lat = wgs2gcj(wgs_lng, wgs_lat)
        d_lng = tmp_lng - gcj_lng
        d_lat = tmp_lat - gcj_lat
        if abs(d_lng) < threshold and abs(d_lat) < threshold:
            return wgs_lng, wgs_lat
        if d_lng > 0:
            p_lng = wgs_lng
        else:
            m_lng = wgs_lng
        if d_lat > 0:
            p_lat = wgs_lat
        else:
            m_lat = wgs_lat
    return wgs_lng, wgs_lat


def distance(lng_a, lat_a, lng_b, lat_b):
    if isinstance(lng_a, Decimal) or isinstance(lng_b, Decimal):
        d = _distance(float(lng_a), float(lat_a), float(lng_b), float(lat_b))
    else:
        d = _distance(lng_a, lat_a, lng_b, lat_b)
    return int(round(d))


def _distance(lng_a, lat_a, lng_b, lat_b):
    pi180 = math.pi / 180
    arc_lat_a = lat_a * pi180
    arc_lat_b = lat_b * pi180
    x = (math.cos(arc_lat_a) * math.cos(arc_lat_b) * math.cos((lng_a - lng_b) * pi180))
    y = math.sin(arc_lat_a) * math.sin(arc_lat_b)
    s = x + y
    if s > 1:
        s = 1
    if s < -1:
        s = -1
    alpha = math.acos(s)
    return alpha * EARTH_RADIUS


def gcj2bd(gcj_lng, gcj_lat):
    if isinstance(gcj_lng, Decimal):
        bd_lng, bd_lat = _gcj2bd(float(gcj_lng), float(gcj_lat))
        bd_lng = Decimal(bd_lng)
        bd_lat = Decimal(bd_lat)
    else:
        bd_lng, bd_lat = _gcj2bd(gcj_lng, gcj_lat)
    return bd_lng, bd_lat


def _gcj2bd(gcj_lng, gcj_lat):
    if out_of_china(gcj_lng, gcj_lat):
        return gcj_lng, gcj_lat

    x = gcj_lng
    y = gcj_lat
    z = math.hypot(x, y) + 0.00002 * math.sin(y * math.pi)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * math.pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat


def bd2gcj(bd_lng, bd_lat):
    if isinstance(bd_lng, Decimal):
        gcj_lng, gcj_lat = _bd2gcj(float(bd_lng), float(bd_lat))
        gcj_lng = Decimal(gcj_lng)
        gcj_lat = Decimal(gcj_lat)
    else:
        gcj_lng, gcj_lat = _bd2gcj(bd_lng, bd_lat)
    return gcj_lng, gcj_lat


def _bd2gcj(bd_lng, bd_lat):
    if out_of_china(bd_lng, bd_lat):
        return bd_lng, bd_lat

    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.hypot(x, y) - 0.00002 * math.sin(y * math.pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * math.pi)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return gcj_lng, gcj_lat


def wgs2bd(wgs_lng, wgs_lat):
    return gcj2bd(*wgs2gcj(wgs_lng, wgs_lat))


def bd2wgs(bd_lng, bd_lat):
    return gcj2wgs(*bd2gcj(bd_lng, bd_lat))
