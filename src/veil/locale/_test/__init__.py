from __future__ import unicode_literals, print_function, division
import __builtin__
from gettext import NullTranslations
from sandal.fixture import fixture
from sandal.fixture import get_executing_test

@fixture
def install_null_translation():
    def clean_up():
        install_null_translation.in_use = False
        del __builtin__.__dict__['_']
    if install_null_translation.in_use:
        return
    install_null_translation.in_use = True
    get_executing_test().addCleanup(clean_up)
    NullTranslations().install(unicode=True)

install_null_translation.in_use = False
