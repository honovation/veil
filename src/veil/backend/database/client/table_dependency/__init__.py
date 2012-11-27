import veil_component

with veil_component.init_component(__name__):
    from .table_dependency import check_table_dependencies

    __all__ = [
        check_table_dependencies.__name__
    ]
