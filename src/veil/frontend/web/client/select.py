from __future__ import unicode_literals, print_function, division
from veil.development.test import get_executing_test

class SelectMixin(object):
    def select(self, name, **kwargs):
        if not self.is_multiple(name):
            self.deselect_all(name)
        elements = self.q('[name="{}"] {}'.format(name, get_option_selector(**kwargs)))
        elements.attr('selected', 'selected')


    def deselect_all(self, name):
        elements = self.q('[name="{}"] option:selected'.format(name), allow_empty=True)
        elements.attr('selected', None)


    def is_selected(self, name, **kwargs):
        element = self.q('[name="{}"] {}'.format(name, get_option_selector(**kwargs)))
        selected = element.attr('selected')
        return selected is not None

    def is_multiple(self, name):
        element = self.q('[name="{}"]'.format(name))
        if element:
            return 'multiple' in element[0].attrib

    def assert_selected(self, name, **kwargs):
        get_executing_test().assertTrue(self.is_selected(name, **kwargs))


def get_option_selector(value=None, css_class=None, text=None):
    selector = 'option'
    if css_class is not None:
        selector += '.{}'.format(css_class)
    if value is not None:
        selector += '[value="{}"]'.format(value)
    if text is not None:
        selector += ":contains('{}')".format(text)
    return selector