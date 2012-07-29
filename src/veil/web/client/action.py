from __future__ import unicode_literals, print_function, division
import httplib

class ActionMixin(object):
    def type(self, name, value):
        selector = 'input[name="{}"]'.format(name)
        if self.exists(selector):
            self.q(selector).attr('value', value)
        else:
            self.q('textarea[name="{}"]'.format(name)).text(value)

    def check(self, name, value):
        self.q('input:radio[name="{}"]:checked'.format(name), allow_empty=True).attr('checked', None)
        self.q('input:radio[name="{name}"][value="{value}"],input:checkbox[name="{name}"][value="{value}"]'.format(
            name=name, value=value)).attr('checked', 'checked')

    def replace_with(self, selector, path):
        new_html = self.get(path).response_text
        self.q(selector).replaceWith(new_html)

    def replace_html(self, selector, path):
        new_html = self.get(path).response_text
        self.q(selector).html(new_html)

    def click_link(self, selector):
        self.get(self.q(selector).attr('href'))

    def follow_redirect(self):
        assert self.page.status_code in [httplib.MOVED_PERMANENTLY, httplib.FOUND]
        return self.get(self.page.response.headers['Location'])