import veil_component
with veil_component.init_component(__name__):
    from .table_dependency import check_table_dependencies
    from .table_dependency import get_writing_table_name

    __all__ = [
        check_table_dependencies.__name__,
        get_writing_table_name.__name__
    ]
