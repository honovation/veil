import veil.component

with veil.component.init_component(__name__):
    from .db2_setting import db2_settings

    __all__ = [
        db2_settings.__name__
    ]

    def init():
        from .adapter import DB2Adapter
        from veil.backend.database.client import register_adapter_class

        register_adapter_class('db2', DB2Adapter)
