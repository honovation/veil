import veil_component

with veil_component.init_component(__name__):
    from .database_client import register_database
    from .database_client import require_database
    from .database_client import transactional
    from .database_client import register_adapter_class

    __all__ = [
        # from database
        register_database.__name__,
        require_database.__name__,
        transactional.__name__,
        register_adapter_class.__name__
    ]

    def init():
        from veil.development.architecture import register_architecture_checker
        from .database_client import check_database_dependencies
        from .table_dependency import update_writable_tables

        register_architecture_checker('DATABASES', check_database_dependencies)
        register_architecture_checker('TABLES', update_writable_tables)
