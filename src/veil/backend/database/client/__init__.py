import veil_component

with veil_component.init_component(__name__):
    from .database_client import register_database
    from .database_client import require_database
    from .database_client import transactional
    from .database_client import register_adapter_class
    from .database_client import EVENT_SQL_EXECUTED
    from .database_client import EVENT_SQL_BATCH_EXECUTED
    from .database_client import EVENT_SQL_QUERIED
    from .table_dependency import get_writing_table_name
    from .database_client_installer import load_database_client_config
    from .database_client_installer import database_client_resource

    __all__ = [
        # from database_client
        register_database.__name__,
        require_database.__name__,
        transactional.__name__,
        register_adapter_class.__name__,
        'EVENT_SQL_EXECUTED',
        'EVENT_SQL_BATCH_EXECUTED',
        'EVENT_SQL_QUERIED',
        # from table_dependency
        get_writing_table_name.__name__,
        # from database_client_installer
        load_database_client_config.__name__,
        database_client_resource.__name__
    ]
