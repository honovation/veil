# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from veil.backend.database.client import *
from veil.model.collection import *
from .region import list_region_name_patterns, parse_address

db = lambda: require_database('ljmall')


class RegionTest(TestCase):
    def setUp(self):
        data = [
            DictObject(code='110000', name='北京市', level=1, has_child=True, has_active_child=True),
            DictObject(code='110115', name='大兴区', level=3, has_child=False, has_active_child=False)
        ]
        db().insert('region', data)

    def tearDown(self):
        db().execute('DELETE FROM region WHERE code IN %(codes)s', codes=('110000', '110115'))

    def test_parse_address(self):
        full_address = '北京市大兴区群英汇大厦四层'
        self.assertEqual('北京市', parse_address(db, full_address).province.name)
        self.assertEqual('大兴区', parse_address(db, full_address).district.name)
        self.assertEqual('群英汇大厦四层', parse_address(db, full_address).address_detail)

    def test_list_region_name_patterns(self):
        region = DictObject(code='110000', name='北京市', level=1)
        self.assertListEqual(list_region_name_patterns(region), ['北京市', '北京'])
        region = DictObject(code='130100', name='石家庄市', level=2)
        self.assertListEqual(list_region_name_patterns(region), ['石家庄市', '石家庄'])
        region = DictObject(code='441803', name='清新区', level=3)
        self.assertListEqual(list_region_name_patterns(region), ['清新区', '清新'])
        region = DictObject(code='130107', name='井陉矿区', level=3)
        self.assertListEqual(list_region_name_patterns(region), ['井陉矿区', '井陉'])
        region = DictObject(code='140203', name='矿区', level=3)
        self.assertListEqual(list_region_name_patterns(region), ['矿区'])
        region = DictObject(code='511132', name='峨边彝族自治县', level=3)
        self.assertListEqual(list_region_name_patterns(region), ['峨边彝族自治县', '峨边'])
        region = DictObject(code='530826', name='江城哈尼族彝族自治县', level=3)
        self.assertListEqual(list_region_name_patterns(region), ['江城哈尼族彝族自治县', '江城'])
        region = DictObject(code='810000', name='香港特别行政区', level=1)
        self.assertListEqual(list_region_name_patterns(region), ['香港特别行政区'])
