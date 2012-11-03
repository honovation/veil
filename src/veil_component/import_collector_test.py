from __future__ import unicode_literals, print_function, division
import unittest
from .import_collector import list_imports

class ListImportsTest(unittest.TestCase):
    def test_import_absolute(self):
        absolute_imports, relative_imports = list_imports(
            """
            import some_package
            """.strip())
        self.assertEqual(['some_package'], absolute_imports)
        self.assertEqual([], relative_imports)

    def test_import_absolute_as(self):
        absolute_imports, relative_imports = list_imports(
            """
            import some_package as sp
            """.strip())
        self.assertEqual(['some_package'], absolute_imports)
        self.assertEqual([], relative_imports)

    def test_import_multiple(self):
        absolute_imports, relative_imports = list_imports(
            """
            import some_package, another_package
            """.strip())
        self.assertEqual(['some_package', 'another_package'], absolute_imports)
        self.assertEqual([], relative_imports)


    def test_from_import_absolute(self):
        absolute_imports, relative_imports = list_imports(
            """
            from some_package import some_function
            """.strip())
        self.assertEqual(['some_package', 'some_package.some_function'], absolute_imports)
        self.assertEqual([], relative_imports)

    def test_from_import_absolute_as(self):
        absolute_imports, relative_imports = list_imports(
            """
            from some_package import some_function as sf
            """.strip())
        self.assertEqual(['some_package', 'some_package.some_function'], absolute_imports)
        self.assertEqual([], relative_imports)

    def test_from_import_absolute_star(self):
        absolute_imports, relative_imports = list_imports(
            """
            from some_package import *
            """.strip())
        self.assertEqual(['some_package', 'some_package.*'], absolute_imports)
        self.assertEqual([], relative_imports)

    def test_from_import_relative(self):
        absolute_imports, relative_imports = list_imports(
            """
            from .internal_module import some_function
            """.strip())
        self.assertEqual([], absolute_imports)
        self.assertEqual([(1, 'internal_module', 'some_function')], relative_imports)

    def test_from_import_relative_multiple_levels(self):
        absolute_imports, relative_imports = list_imports(
            """
            from ..internal_module import some_function
            """.strip())
        self.assertEqual([], absolute_imports)
        self.assertEqual([(2, 'internal_module', 'some_function')], relative_imports)

    def test_from_import_multiple_sub_modules(self):
        absolute_imports, relative_imports = list_imports(
            """
            from some_package import some_function as sf, another_function as af
            """.strip())
        self.assertEqual({'some_package', 'some_package.some_function', 'some_package.another_function'},
            set(absolute_imports))
        self.assertEqual([], relative_imports)

    def test_mixed_case(self):
        lines = [
            'import yet_another_package',
            'from some_package import some_function as sf, another_function as af',
            'import another_package',
            'from ..internal_module import some_function']
        absolute_imports, relative_imports = list_imports('\n'.join(lines))
        self.assertEqual({'some_package', 'some_package.some_function', 'some_package.another_function',
                          'another_package', 'yet_another_package'}, set(absolute_imports))
        self.assertEqual([(2, 'internal_module', 'some_function')], relative_imports)





