import veil_component
with veil_component.init_component(__name__):
    __all__ = []

    def init():
        from veil.backend.database.client import register_adapter_class
        from .adapter import MSSQLAdapter

        register_adapter_class(MSSQLAdapter.type, MSSQLAdapter)
