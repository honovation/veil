from __future__ import unicode_literals, print_function, division
import hashlib
from StringIO import StringIO


__all__ = [
    'iter_file_in_chunks',
    'calculate_file_md5_hash',
    'ContextAwareStringIO',
]

def iter_file_in_chunks(file_object, chunk_size=8192):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 8k."""
    return iter(lambda : file_object.read(chunk_size), b'')


def calculate_file_md5_hash(file_object, reset_position=False, hex=True):
    """ Calculate the md5 hash for this file.

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

# TODO: remove this and use cStringIO.StringIO or StringIO.StringIO when cStringIO.StringIO or StringIO.StringIO becomes context aware in the new version of python
class ContextAwareStringIO(StringIO):
    # Context management protocol
    def __enter__(self):
        if self.closed:
            raise ValueError('I/O operation on closed file')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
