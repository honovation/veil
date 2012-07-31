from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
from veil.environment.layout import VEIL_HOME
from veil.backend.path import *
from veil.frontend.cli import *
from veil.backend.shell import *
from .i18n import LOCALE_DIR

@script('extract')
def extract_translation():
    LOCALE_DIR.mkdir()
    shell_execute('pybabel extract --omit-header -o {output} -F {mapping_file} {input}'.format(
        input=VEIL_HOME / 'src',
        output=LOCALE_DIR / 'messages.po',
        mapping_file=LOCALE_DIR / 'BABEL_MAPPING_FILE'
    ))


@script('init')
def execute_init_translation(*argv):
    argument_parser = ArgumentParser('Initialize localization *.po file for specific locale')
    argument_parser.add_argument('--locale', default='zh')
    args = argument_parser.parse_args(argv)
    init_translation(args.locale)


def init_translation(locale):
    shell_execute('pybabel init -d {output} -i {input} -l {locale}'.format(
        input=LOCALE_DIR / 'messages.po',
        output=LOCALE_DIR,
        locale=locale
    ))


@script('update')
def execute_update_translation(*argv):
    argument_parser = ArgumentParser('Update localization *.po file for specific locale')
    argument_parser.add_argument('--locale', default='zh')
    args = argument_parser.parse_args(argv)
    update_translation(args.locale)


def update_translation(locale):
    shell_execute('pybabel update -i {input} -d {output} -l {locale}'.format(
        input=LOCALE_DIR / 'messages.po',
        output=LOCALE_DIR,
        locale=locale
    ))


@script('compile')
def execute_compile_translation(*argv):
    argument_parser = ArgumentParser('Compile localization *.po file for specific locale')
    argument_parser.add_argument('--locale', default='zh')
    args = argument_parser.parse_args(argv)
    compile_translation(args.locale)


def compile_translation(locale):
    shell_execute('pybabel compile -d {input} -l {locale} -f'.format(
        input=LOCALE_DIR,
        locale=locale
    ))