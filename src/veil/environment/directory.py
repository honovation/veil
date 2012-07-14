import logging
import os.path
from .metadata import ensure_metadata

LOGGER = logging.getLogger(__name__)

def create_directory(path, owner='root', group='root', mode=0755, recursive=False):
    if not os.path.exists(path):
        LOGGER.info("Creating directory %s" % path)
        if recursive:
            os.makedirs(path, mode or 0755)
        else:
            os.mkdir(path, mode or 0755)
    ensure_metadata(path, owner, group, mode=mode)

