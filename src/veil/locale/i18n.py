from __future__ import unicode_literals, print_function, division
import contextlib
from gettext import NullTranslations
from logging import getLogger
from babel.core import Locale
from babel.support import Translations
from sandal.template import require_current_translations_being
from sandal.const import consts
from sandal.test import get_executing_test
from veil.environment.layout import VEIL_HOME

LOGGER = getLogger(__name__)
consts.LOCALE_DIR = VEIL_HOME / 'locale'

def get_locale(*codes):
    locale = None
    for code in codes:
        try:
            locale = Locale.parse(code.replace('-', '_'))
        except:
            LOGGER.exception('Cannot parse locale from the given locale identifier: {}'.format(code))
            continue
        else:
            break
    return locale

DEFAULT_LOCALE = get_locale('zh_CN') # get_locale('zh_CN')
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
    return Translations.load(consts.LOCALE_DIR, locales=locale)


def get_current_locale():
    return current_locales[-1] if current_locales else None


def get_default_locale():
    return DEFAULT_LOCALE


def _(*args, **kwargs):
# to supress the warning of pycharm
    from __builtin__ import _

    return _(*args, **kwargs)


def install_null_translation():
    import __builtin__

    def clean_up():
        del __builtin__.__dict__['_']

    executing_test = get_executing_test(optional=True)
    if executing_test:
        executing_test.addCleanup(clean_up)
    NullTranslations().install(unicode=True)
