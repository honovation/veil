# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from veil.backend.database.client import *
from veil.model.collection import *
from .region import list_region_name_patterns, parse_address

db = lambda: require_database('ljmall')


class RegionTest(TestCase):
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

    def test_parse_address(self):
        full_address = '北京市大兴区群英汇大厦四层'
        self.assertEqual('北京市', parse_address(db, full_address).province.name)
        self.assertEqual('大兴区', parse_address(db, full_address).district.name)
        self.assertEqual('群英汇大厦四层', parse_address(db, full_address).address_detail)
        full_address = '河北省廊坊市固安县固安县城关派出所'
        self.assertEqual('河北省', parse_address(db, full_address).province.name)
        self.assertEqual('廊坊市', parse_address(db, full_address).city.name)
        self.assertEqual('固安县', parse_address(db, full_address).district.name)
        self.assertEqual('固安县城关派出所', parse_address(db, full_address).address_detail)
        full_address = '广东省中山市古镇开元灯配件城F区255'
        self.assertEqual('广东省', parse_address(db, full_address).province.name)
        self.assertEqual('中山市', parse_address(db, full_address).city.name)
        self.assertEqual('古镇开元灯配件城F区255', parse_address(db, full_address).address_detail)

