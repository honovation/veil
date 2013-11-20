from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from .numencode import num2code, code2num, normalize


class NumEncodeTest(TestCase):
    def test(self):
        self.assertEqual(0, code2num(num2code(0)))
        self.assertEqual(1, code2num(num2code(1, split=3)))
        self.assertEqual(16, code2num(num2code(16)))
        self.assertEqual(17, code2num(num2code(17, split=4)))
        self.assertEqual(2 ** 32, code2num(num2code(2 ** 32, split=3)))
        self.assertEqual(2 ** 32 - 1, code2num(num2code(2 ** 32 - 1, split=3)))
        self.assertEqual(2 ** 32 + 1, code2num(num2code(2 ** 32 + 1, split=3)))
        self.assertEqual(2 ** 64, code2num(num2code(2 ** 64, split=4)))
        self.assertEqual(2 ** 64 - 1, code2num(num2code(2 ** 64 - 1)))
        self.assertEqual(2 ** 64 + 1, code2num(num2code(2 ** 64 + 1)))

    def test_normalize(self):
        self.assertEqual('WFY8ABB8', normalize('WFY8ABB8'))
        self.assertEqual('WFY8ABB8', normalize('WFY-8AB-B80'))
        with self.assertRaises(ValueError):
            normalize('WFY8ABB08')
