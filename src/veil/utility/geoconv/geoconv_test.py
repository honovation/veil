from __future__ import unicode_literals, print_function, division
import timeit
from veil.development.test import *
from .geoconv import *

TESTS = [
    # wgs_lng, wgs_lat, gcj_lng, gcj_lat
    (Decimal('121.5272106'), Decimal('31.1774276'), Decimal('121.531541859215'), Decimal('31.17530398364597')),  # shanghai
    (Decimal('113.912316'), Decimal('22.543847'), Decimal('113.9171764808363'), Decimal('22.540796131694766')),  # shenzhen
    (Decimal('116.377817'), Decimal('39.911954'), Decimal('116.38404722455657'), Decimal('39.91334545536069'))  # beijing
]

TESTS_bd = [
    # bd_lng, bd_lat, wgs_lng, wgs_lat
    (Decimal('120.019809'), Decimal('29.199786'), Decimal('120.00877901149691'), Decimal('29.196131605295484')),
    (Decimal('120.036455'), Decimal('29.210504'), Decimal('120.0253853970846'), Decimal('29.206795749156136'))
]


class GeoConvTest(TestCase):
    def setUp(self):
        super(GeoConvTest, self).setUp()

    def test_wgs2gcj(self):
        for wgs_lng, wgs_lat, gcj_lng, gcj_lat in TESTS:
            ret = wgs2gcj(wgs_lng, wgs_lat)
            self.assertAlmostEqual(ret[0], gcj_lng, 6)
            self.assertAlmostEqual(ret[1], gcj_lat, 6)

    def test_bd2wgs(self):
        for bd_lng, bd_lat, wgs_lng, wgs_lat in TESTS_bd:
            ret = bd2wgs(bd_lng, bd_lat)
            self.assertAlmostEqual(ret[0], wgs_lng, 6)
            self.assertAlmostEqual(ret[1], wgs_lat, 6)

    def test_gcj2wgs(self):
        for wgs_lng, wgs_lat, gcj_lng, gcj_lat in TESTS:
            ret = gcj2wgs(gcj_lng, gcj_lat)
            self.assertLess(distance(ret[0], ret[1], wgs_lng, wgs_lat), 5)

    def test_gcj2wgs_exact(self):
        for wgs_lng, wgs_lat, gcj_lng, gcj_lat in TESTS:
            ret = gcj2wgs_exact(gcj_lng, gcj_lat)
            self.assertLess(distance(ret[0], ret[1], wgs_lng, wgs_lat), .5)

    @skip('ignored performance test')
    def test_z_speed(self):
        n = 100000
        tests = (
            ('wgs2gcj', lambda: wgs2gcj(TESTS[0][0], TESTS[0][1])),
            ('gcj2wgs', lambda: gcj2wgs(TESTS[0][0], TESTS[0][1])),
            ('gcj2wgs_exact', lambda: gcj2wgs_exact(TESTS[0][0], TESTS[0][1])),
            ('distance', lambda: distance(*TESTS[0]))
        )
        print('\n' + '=' * 30)
        for name, func in tests:
            sec = timeit.timeit(func, number=n)
            print('%s\t%.2f ns/op' % (name, sec * 1e9 / n))
