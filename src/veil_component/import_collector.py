from __future__ import unicode_literals, print_function, division
import ast
import traceback


def list_imports(source_code, filename=None):
    try:
        tree = ast.parse(source_code, filename)
    except Exception:
        traceback.print_exc()
        return [], []
    import_collector = ImportCollector()
    import_collector.visit(tree)
    return import_collector.absolute_imports, import_collector.relative_imports


class ImportCollector(ast.NodeVisitor):
    def __init__(self):
        super(ImportCollector, self).__init__()
        self.absolute_imports = []
        self.relative_imports = []

    def generic_visit(self, node):
        for child_node in ast.iter_child_nodes(node):
            self.visit(child_node)

    def visit_Import(self, node):
        alias_nodes = list(ast.iter_child_nodes(node))
        for alias_node in alias_nodes:
            alias_fields = dict(ast.iter_fields(alias_node))
            self.absolute_imports.append(alias_fields['name'])

    def visit_ImportFrom(self, node):
        fields = dict(ast.iter_fields(node))
        alias_nodes = list(ast.iter_child_nodes(node))
        for alias_node in alias_nodes:
            alias_fields = dict(ast.iter_fields(alias_node))
            if fields['level'] == 0:
                # from a import b
                # it might mean a.b is a module
                # or b might be a function of a module
                self.absolute_imports.append(fields['module'])
                self.absolute_imports.append('{}.{}'.format(fields['module'], alias_fields['name']))
            else:
                self.relative_imports.append((fields['level'], fields['module'], alias_fields['name']))