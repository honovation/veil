import veil_component

with veil_component.init_component(__name__):
    __all__ = []

    def init():
        from .adapter import MySQLAdapter
        from veil.backend.database.client import register_adapter_class

        register_adapter_class('mysql', MySQLAdapter)