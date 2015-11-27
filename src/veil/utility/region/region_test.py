# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from veil.model.collection import *
from .region import list_region_name_patterns


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
        region = DictObject(code='710000', name='台湾省', level=1)
        self.assertListEqual(list_region_name_patterns(region), ['台湾省', '台湾'])
        region = DictObject(code='810000', name='香港特别行政区', level=1)
        self.assertListEqual(list_region_name_patterns(region), ['香港特别行政区', '香港'])
