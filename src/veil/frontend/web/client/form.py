from __future__ import unicode_literals, print_function, division
from pyquery import PyQuery

class FormMixin(object):
    def serialize_form(self, selector='form:not(.side-form)', form_element=None):
        assert selector or form_element
        form = Form()
        form_element = form_element or self.q(selector)
        form.action = form_element.attr('action')
        form.method = form_element.attr('method') or 'GET'
        for input_element in form_element.find('input'):
            input_element = PyQuery(input_element)
            if input_element.attr('type') in ['checkbox', 'radio']:
                if input_element.attr('checked') is not None:
                    form.add_argument(input_element.attr('name'), input_element.attr('value') or 'on')
            else:
                form.add_argument(input_element.attr('name'), input_element.attr('value'))
        for select_element in form_element.find('select'):
            select_element = PyQuery(select_element)
            for selected_option_element in select_element.find('option:selected'):
                selected_option_element = PyQuery(selected_option_element)
                form.add_argument(select_element.attr('name'), selected_option_element.attr('value'))
        for text_area_element in form_element.find('textarea'):
            text_area_element = PyQuery(text_area_element)
            form.add_argument(text_area_element.attr('name'), text_area_element.text())
        return form

    def submit_form(self, *url_segments, **kwargs):
        action = kwargs.pop('action', None)
        form = kwargs.pop('form', None)
        form = form or self.serialize_form(kwargs.get('selector', 'form:not(.side-form)'))
        kwargs['method'] = kwargs.get('method') or form.method
        kwargs['arguments'] = form.arguments
        url = action or ''.join([str(url_segment) for url_segment in url_segments]) or kwargs['form']
        return self.fetch(url, **kwargs)

class Form(object):
    def __init__(self):
        self.action = None
        self.method = 'GET'
        self.arguments = {}

    def add_argument(self, name, value):
        if name:
            self.arguments.setdefault(name, []).append(value or '')