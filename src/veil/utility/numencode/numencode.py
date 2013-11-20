# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import re
from veil.utility.misc import *


SYMBOLS = 'Y9KCW4LGP3F2BHJ7RVA8SUZEXQ5ND6MT' # The encoded symbol space consists of digits and letters without I, O, 1 and 0
BASE = len(SYMBOLS)
ENCODE_SYMBOLS = {i: ch for (i, ch) in enumerate(SYMBOLS)}
DECODE_SYMBOLS = {ch: i for (i, ch) in enumerate(SYMBOLS)}
VALID_SYMBOLS = re.compile('^[{}]+$'.format(SYMBOLS))
PADDING_SYMBOL = '0'
assert PADDING_SYMBOL not in SYMBOLS


def num2code(number, split=0, width=10):
    if number < 0:
        raise ValueError('number <{}> is not a positive integer'.format(number))
    if split < 0:
        raise ValueError('split <{}> is not a positive integer'.format(split))
    number = int('1{}'.format(unicode(number).zfill(width)[::-1]))
    code = []
    while number > 0:
        number, remainder = divmod(number, BASE)
        code.append(ENCODE_SYMBOLS[remainder])
    code = ''.join(code[::-1])
    if split:
        code = '-'.join(chunks(code, split, padding=True, padding_element=PADDING_SYMBOL))
    return code


def code2num(code):
    code = normalize(code)
    number = 0
    for symbol in code:
        number = number * BASE + DECODE_SYMBOLS[symbol]
    return int(unicode(number)[1:][::-1])


def normalize(code):
    code_ = code.rstrip(PADDING_SYMBOL).replace('-', '').upper()
    if not VALID_SYMBOLS.match(code_):
        raise ValueError('code <{}> contains invalid characters'.format(code))
    return code_
