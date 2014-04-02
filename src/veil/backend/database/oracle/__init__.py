import veil_component

with veil_component.init_component(__name__):
    def init():
        from .adapter import OracleAdapter
        from veil.backend.database.client import register_adapter_class

        register_adapter_class('oracle', OracleAdapter)