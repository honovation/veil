from __future__ import unicode_literals, print_function, division


class QueryMixin(object):
    def q(self, selector, allow_empty=False):
        elements = self.page.dom(str(selector))
        if not allow_empty and len(elements) == 0:
            raise Exception('{} not found in {}'.format(selector, self.page.dom))
        return elements


    def assert_exists(self, selector):
        self.q(selector)


    def assert_not_exist(self, selector):
        if self.exists(selector):
            raise Exception('{} found in {}'.format(selector, self.page.dom))

    def exists(self, selector):
        return len(self.q(selector, allow_empty=True)) > 0
