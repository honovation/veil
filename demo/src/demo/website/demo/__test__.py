from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.development.browser import *

__import__('demo.website.demo.server')

class DemoWebsiteTest(TestCase):
    def test(self):
        start_website_and_browser(
            'demo', '/',
            ["""
            before = $('.list-items-element-widget').length;
            $('input[name=name]').val('hello');
            $('#new-item-widget button[type=submit]').click();
            veil.waitUntil(function(){
                return $('.list-items-element-widget').length == before + 1;
            }, veil.stopTest);
            """])
