from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.model.event import *
from veil.utility.memoize import *

EVENT_NEW_WEBSITE = define_event('new-website')

_config = {}
overridden_website_configs = {}

HTTP_STANDARD_PORT = 80
HTTPS_STANDARD_PORT = 443


def register_website_config(purpose):
    add_application_sub_resource('{}_website'.format(purpose), lambda config: website_resource(purpose=purpose, config=config))

    class WebsiteConfig(object):
        def __init__(self, purpose):
            self._purpose = purpose

        @property
        def purpose(self):
            return self._purpose

        @property
        def url(self):
            return get_website_url(self._purpose)

        @property
        def domain(self):
            return get_website_domain(self._purpose)

        @property
        def parent_domain(self):
            return get_website_parent_domain(self._purpose)

    return WebsiteConfig(purpose)


@event(EVENT_NEW_WEBSITE)
def on_new_website(website):
    add_application_sub_resource('{}_website'.format(website), lambda config: website_resource(purpose=website, config=config))


@composite_installer
def website_resource(purpose, config):
    return [file_resource(path=VEIL_ETC_DIR / '{}-website.cfg'.format(purpose), content=render_config('website.cfg.j2', config=config))]


def website_config(purpose):
    return _config.setdefault(purpose, load_website_config(purpose))


def load_website_config(purpose):
    try:
        config = load_config_from(VEIL_ETC_DIR / '{}-website.cfg'.format(purpose), 'domain', 'domain_port', 'domain_scheme', 'start_port', 'locale',
                                  'master_template_directory', 'prevents_xsrf', 'recalculates_static_file_hash', 'process_page_javascript',
                                  'process_page_stylesheet', 'clears_template_cache')
        config.domain_port = int(config.domain_port)
        config.start_port = int(config.start_port)
        config.prevents_xsrf = unicode(True) == config.prevents_xsrf
        config.recalculates_static_file_hash = unicode(True) == config.recalculates_static_file_hash
        config.process_page_javascript = unicode(True) == config.process_page_javascript
        config.process_page_stylesheet = unicode(True) == config.process_page_stylesheet
        config.clears_template_cache = unicode(True) == config.clears_template_cache
    except IOError:
        if not VEIL_ENV.is_test:
            raise
        config = DictObject()
    if VEIL_ENV.is_test:
        config.update(overridden_website_configs.get(purpose, {}))
    return config


def override_website_config(purpose, **overrides):
    get_executing_test().addCleanup(overridden_website_configs.clear)
    overridden_website_configs.setdefault(purpose, {}).update(overrides)


@memoize
def get_website_url(purpose):
    config = website_config(purpose)
    if config.domain_port in {HTTP_STANDARD_PORT, HTTPS_STANDARD_PORT}:
        return '{}://{}'.format(config.domain_scheme, config.domain)
    else:
        return '{}://{}:{}'.format(config.domain_scheme, config.domain, config.domain_port)


@memoize
def get_website_domain(purpose):
    return website_config(purpose).domain


@memoize
def get_website_parent_domain(purpose):
    parts = get_website_domain(purpose).split('.')[1:]
    if parts[0].lower() in {'dev', 'test', 'staging', 'uat', 'prod'}:
        parts = parts[1:]
    return '.'.join(parts)
