from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.model.collection import *
from veil.environment.setting import *
from veil.development.test import *
from veil.model.event import *
from .routing import *

overriden_website_configs = {}


@event(EVENT_NEW_WEBSITE)
def on_new_website(website):
    add_application_sub_resource(
        '{}_website'.format(website),
        lambda config: website_resource(purpose=website, config=config))


@composite_installer
def website_resource(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / '{}-website.cfg'.format(purpose), content=render_config(
        'website.cfg.j2', config=config)))
    return resources


def load_website_config(purpose):
    try:
        config = load_config_from(VEIL_ETC_DIR / '{}-website.cfg'.format(purpose),
            'domain', 'domain_port', 'start_port', 'secure_cookie_salt', 'secure_hash_salt',
            'master_template_directory', 'prevents_xsrf', 'recalculates_static_file_hash', 'clears_template_cache')
        config.domain_port = int(config.domain_port)
        config.start_port = int(config.start_port)
        config.prevents_xsrf = unicode(True) == config.prevents_xsrf
        config.recalculates_static_file_hash = unicode(True) == config.recalculates_static_file_hash
        config.clears_template_cache = unicode(True) == config.clears_template_cache
    except IOError, e:
        if 'test' == VEIL_SERVER:
            config = DictObject()
        else:
            raise
    if 'test' == VEIL_SERVER:
        config.update(overriden_website_configs.get(purpose, {}))
    return config


def override_website_config(purpose, **overrides):
    get_executing_test().addCleanup(overriden_website_configs.clear)
    overriden_website_configs.setdefault(purpose, {}).update(overrides)


def get_website_url_prefix(purpose):
    config = load_website_config(purpose)
    return 'http://{}:{}'.format(config.domain, config.domain_port)