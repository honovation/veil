# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import hashlib
import traceback
from decimal import ROUND_HALF_UP, Decimal
from veil.utility.encoding import to_unicode

TWO_PLACES = Decimal('0.01')

def unique(iterable, idfunc=lambda x:x):
    seen = set()
    return [x for x in iterable if idfunc(x) not in seen and not seen.add(idfunc(x))]


def chunks(seq, size, padding=False, padding_element=None):
    """
    Yield successive n-sized chunks from seq.
    """
    if padding:
        remain = len(seq) % size
        if remain != 0:
            for i in xrange(0, size - remain):
                seq.append(padding_element)
    for i in xrange(0, len(seq), size):
        yield seq[i:i+size]


def iter_file_in_chunks(file_object, chunk_size=8192):
    """
    Lazy function (generator) to read a file piece by piece.
    Default chunk size: 8k.
    """
    return iter(lambda: file_object.read(chunk_size), b'')


def calculate_file_md5_hash(file_object, reset_position=False, hex=True):
    """
    Calculate the md5 hash for this file.
    This reads through the entire file.
    """
    assert file_object is not None and file_object.tell() == 0
    try:
        m = hashlib.md5()
        for chunk in iter_file_in_chunks(file_object):
            m.update(chunk)
        return m.hexdigest() if hex else m.digest()
    finally:
        if reset_position:
            file_object.seek(0)


def round_money(d):
    return d.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def remove_elements_without_value_from_dict(d):
    for key in list(d.keys()):
        if not d[key]:
            del d[key]


def format_exception(exception_info):
    return to_unicode(b''.join(traceback.format_exception(*exception_info)))
