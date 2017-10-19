# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.development.test import TestCase
from .routing import PathTemplate
from .routing import parse_user_agent


class PathTemplateTest(TestCase):
    def test_simple_template(self):
        self.assertEqual('/some$', PathTemplate('/some', {}).translate_to_regex())

    def test_with_dot(self):
        self.assertEqual('/some\.html$', PathTemplate('/some.html', {}).translate_to_regex())

    def test_with_arg(self):
        self.assertEqual(r'/some/(?P<id>.*)$', PathTemplate('/some/{{ id }}', {'id':'.*'}).translate_to_regex())

    def test_not_enough_params(self):
        self.assertRaises(Exception, lambda: PathTemplate('/some/{{ id }}', {}))

    def test_too_many_params(self):
        self.assertRaises(Exception, lambda: PathTemplate('/some', {'id': '.*'}))


class ParseUserAgentTest(TestCase):
    def test_user_agent_with_bad_byte_sequences(self):
        ua = parse_user_agent(b'Rajax/1 Lenovo_A820t/A820t Android/4.1.2 Display/Lenovo_A820t_S115_AnZhiæ <96>å®¿ Eleme/4.4.1 ID/ea14ab53-4c54-3645-bac9-a81b63d6e7f1; KERNEL_VERSION:3.4.5 API_Level:16 Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; Lenovo A820t Build/JZO54K) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30')
        self.assertFalse(b'MicroMessenger' in ua.ua_string, 'it should not from weixin')

    def test_user_agent_with_wx(self):
        ua = parse_user_agent(b'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_2 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Mobile/15A421 MicroMessenger/6.5.18 NetType/WIFI Language/zh_CN')
        self.assertTrue(ua.is_from_weixin, 'it should be from weixin')
