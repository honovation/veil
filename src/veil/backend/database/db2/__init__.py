import veil_component
with veil_component.init_component(__name__):
    __all__ = []

    def init():
        from veil.backend.database.client import register_adapter_class
        from .adapter import DB2Adapter

        register_adapter_class(DB2Adapter.type, DB2Adapter)
