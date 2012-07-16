from __future__ import unicode_literals, print_function, division
import logging
import os.path
from .metadata import ensure_metadata

LOGGER = logging.getLogger(__name__)

def create_file(path, content, owner='root', group='root', mode=0644):
    write = False
    if not os.path.exists(path):
        write = True
        reason = "it doesn't exist"
    else:
        if content is not None:
            with open(path, "rb") as fp:
                old_content = fp.read()
            if content != old_content:
                write = True
                reason = "contents don't match"

    if write:
        LOGGER.info("Writing %s because %s" % (path, reason))
        with open(path, "wb") as fp:
            if content:
                fp.write(content)

    ensure_metadata(path, owner, group, mode = mode)

