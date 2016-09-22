# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from decimal import Decimal
from math import sqrt, pow, sin, cos, atan2

X_PI = Decimal('3.14159265358979324') * Decimal('3000.0') / Decimal('180.0')


# reference: http://www.jianshu.com/p/0fe30fcd4ae7
def convert_from_gcj02_to_baidu(coords):
    decrypted_coords = []
    for coord in coords:
        x, y = coord
        z = Decimal(sqrt(pow(x, 2) + pow(y, 2))) + Decimal('0.00002') * Decimal(sin(y * X_PI))
        theta = Decimal(atan2(y, x)) + Decimal('0.000003') * Decimal(cos(x * X_PI))
        decrypted_coords.append((Decimal(z * Decimal(cos(theta))) + Decimal('0.0065'), Decimal(z * Decimal(sin(theta))) + Decimal('0.006')))
    return decrypted_coords


def convert_from_baidu_to_gcj02(coords):
    decrypted_coords = []
    for coord in coords:
        x = coord[0] - Decimal('0.0065')
        y = coord[1] - Decimal('0.006')
        z = Decimal(sqrt(pow(x, 2) + pow(y, 2))) - Decimal('0.00002') * Decimal(sin(y * X_PI))
        theta = Decimal(atan2(y, x)) - Decimal('0.000003') * Decimal(cos(x * X_PI))
        decrypted_coords.append((Decimal(z * Decimal(cos(theta))), Decimal(z * Decimal(sin(theta)))))
    return decrypted_coords
