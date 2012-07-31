from __future__ import unicode_literals, print_function, division
from pyquery import PyQuery
from sandal.test import TestCase
from ..form import FormMixin

class SerializeFormTest(TestCase):
    def test_empty_form(self):
        form = FormMixin().serialize_form(form_element=PyQuery('<form action="/hello"></form>'))
        self.assertEqual('/hello', form.action)
        self.assertEqual('GET', form.method)
        self.assertEqual({}, form.arguments)

    def test_one_text_input(self):
        self.assertEqual({'name': ['value']}, self.serialize_form(
            '<input type="text" name="name" value="value"/>'
        ))

    def test_not_only_input(self):
        self.assertEqual({'name': ['value']}, self.serialize_form("""
            <label for="some-field">Some Field: </label>
            <input id="some-field" type="text" name="name" value="value"/>
        """))

    def test_select(self):
        self.assertEqual({'name': ['value1']}, self.serialize_form("""
            <select name="name">
            <option value="value1" selected>label1</option>
            <option value="value2">label2</option>
            </select>
        """))

    def test_checkbox(self):
        self.assertEqual({'name': ['value']}, self.serialize_form(
            '<input type="checkbox" name="name" value="value" checked/>'
        ))
        self.assertEqual({'name': ['on']}, self.serialize_form(
            '<input type="checkbox" name="name" checked/>'
        ))
        self.assertEqual({'name': ['on']}, self.serialize_form(
            '<input type="checkbox" name="name" checked="true"/>'
        ))
        self.assertEqual({'name': ['on']}, self.serialize_form(
            '<input type="checkbox" name="name" checked="false"/>'
        ))
        self.assertEqual({'name': ['on']}, self.serialize_form(
            '<input type="checkbox" name="name" checked="on"/>'
        ))
        self.assertEqual({'name': ['on']}, self.serialize_form(
            '<input type="checkbox" name="name" checked="off"/>'
        ))
        self.assertEqual({}, self.serialize_form(
            '<input type="checkbox" name="name"/>'
        ))
        self.assertEqual({}, self.serialize_form(
            '<input type="checkbox" name="name" value="value"/>'
        ))

    def test_radio(self):
        self.assertEqual({'name': ['value']}, self.serialize_form(
            '<input type="radio" name="name" value="value" checked/>'
        ))
        self.assertEqual({'name': ['on']}, self.serialize_form(
            '<input type="radio" name="name" checked/>'
        ))
        self.assertEqual({}, self.serialize_form(
            '<input type="radio" name="name"/>'
        ))

    def test_text_area(self):
        self.assertEqual({'name': ['value']}, self.serialize_form(
            '<textarea name="name">value</textarea>'
        ))

    def test_indirect_input(self):
        self.assertEqual({'name': ['value']}, self.serialize_form(
            '<ul><li><input type="text" name="name" value="value"/><li></ul>'
        ))

    @staticmethod
    def serialize_form(inner_html):
        html = '<form>{}</form>'.format(inner_html)
        form = FormMixin().serialize_form(form_element=PyQuery(html))
        return form.arguments