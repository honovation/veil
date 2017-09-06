# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from veil.model.collection import *
from .qcloud_ocr import sign_sha1


class TestQcloudOCR(TestCase):

    def test_sign_sha1(self):
        config = DictObject(appid=1252821871, secret_id='AKIDgaoOYh2kOmJfWVdH4lpfxScG2zPLPGoK', secret_key='nwOKDouy5JctNOlnere4gkVoOUz5EYAb')
        bucket_name = 'tencentyun'
        current_timestamp = 1436077115
        expired_timestamp = current_timestamp + 2592000
        once_sign_expired_timestamp = 0
        rand = 11162
        fileid = 'tencentyunSignTest'
        no_fileid = ''

        multi_sign_without_fileid_expected = 'p2Y5iIYyBmQNfUvPe3e1sxEN/rZhPTEyNTI4MjE4NzEmYj10ZW5jZW50eXVuJms9QUtJRGdhb09ZaDJrT21KZldWZEg0bHBmeFNjRzJ6UExQR29LJmU9MTQzODY2OTExNSZ0PTE0MzYwNzcxMTUmcj0xMTE2MiZ1PTAmZj0='
        multi_sign_without_fileid_sign = sign_sha1(config.appid, bucket_name, config.secret_id, config.secret_key, expired_timestamp, current_timestamp, rand, no_fileid)
        self.assertEqual(multi_sign_without_fileid_expected, multi_sign_without_fileid_sign)

        multi_sign_with_fileid_expected = 'Tt9IYBG4j1TpO/9M6M9TokVJrKhhPTEyNTI4MjE4NzEmYj10ZW5jZW50eXVuJms9QUtJRGdhb09ZaDJrT21KZldWZEg0bHBmeFNjRzJ6UExQR29LJmU9MTQzODY2OTExNSZ0PTE0MzYwNzcxMTUmcj0xMTE2MiZ1PTAmZj10ZW5jZW50eXVuU2lnblRlc3Q='
        multi_sign_with_fileid_sign = sign_sha1(config.appid, bucket_name, config.secret_id, config.secret_key, expired_timestamp, current_timestamp, rand, fileid)
        self.assertEqual(multi_sign_with_fileid_expected, multi_sign_with_fileid_sign)

        once_sign_with_fileid_expected = 'ewXflzgpQON2bmrX6uJ5Yr0zuOphPTEyNTI4MjE4NzEmYj10ZW5jZW50eXVuJms9QUtJRGdhb09ZaDJrT21KZldWZEg0bHBmeFNjRzJ6UExQR29LJmU9MCZ0PTE0MzYwNzcxMTUmcj0xMTE2MiZ1PTAmZj10ZW5jZW50eXVuU2lnblRlc3Q='
        once_sign_with_fileid_sign = sign_sha1(config.appid, bucket_name, config.secret_id, config.secret_key, once_sign_expired_timestamp, current_timestamp, rand, fileid)
        self.assertEqual(once_sign_with_fileid_expected, once_sign_with_fileid_sign)

