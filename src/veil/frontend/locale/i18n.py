from __future__ import unicode_literals, print_function, division
import contextlib
from gettext import NullTranslations
from logging import getLogger
from babel.core import Locale
from babel.support import Translations
import sys
from veil.environment import VEIL_HOME
from veil.development.test import *
from veil.frontend.template import *
from veil.model.event import *
from veil.server.process import *

LOGGER = getLogger(__name__)
LOCALE_DIR = VEIL_HOME / 'locale'

def get_locale(*codes):
    locale = None
    for code in codes:
        try:
            locale = Locale.parse('zh_Hans_CN.UTF-8' if code.lower() in ('zh-cn', 'zh_cn', 'cn') else code.replace('-', '_'))
        except Exception:
            LOGGER.exception('Cannot parse locale from the given locale identifier: %(code)s, %(codes)s', {
                'code': code,
                'codes': codes
            })
            continue
        else:
            break
    return locale

DEFAULT_LOCALE = get_locale('zh_Hans_CN.UTF-8')
assert DEFAULT_LOCALE is not None

current_locales = []

@contextlib.contextmanager
def require_current_locale_being(locale):
    current_locales.append(locale)
    try:
        translations = load_translations(locale=locale)
        translations.install(unicode=True)
        with require_current_translations_being(translations):
            yield
    finally:
        NullTranslations().install(unicode=True)
        current_locales.pop()


def require_current_locale_being_default():
    return require_current_locale_being(DEFAULT_LOCALE)


def load_translations(locale):
    return Translations.load(LOCALE_DIR, locales=locale)


def get_current_locale():
    return current_locales[-1] if current_locales else DEFAULT_LOCALE


def get_default_locale():
    return DEFAULT_LOCALE


def _(*args, **kwargs):
# to supress the warning of pycharm
    return sys.modules['__builtin__']._(*args, **kwargs)

@event(EVENT_PROCESS_SETUP)
@test_hook
def install_null_translation():
    def clean_up():
        del sys.modules['__builtin__'].__dict__['_']

    executing_test = get_executing_test(optional=True)
    if executing_test:
        executing_test.addCleanup(clean_up)
    NullTranslations().install(unicode=True)
