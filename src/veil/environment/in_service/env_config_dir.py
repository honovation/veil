# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

ENV_CONFIG_DIR = None


def set_env_config_dir(config_dir):
    global ENV_CONFIG_DIR
    ENV_CONFIG_DIR = config_dir


def get_env_config_dir():
    global ENV_CONFIG_DIR
    return ENV_CONFIG_DIR
