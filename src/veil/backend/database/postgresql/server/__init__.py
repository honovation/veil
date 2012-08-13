import sandal.component

with sandal.component.init_component(__name__):
    from .setting import postgresql_program

    __all__ = [
        postgresql_program.__name__
    ]

    def init():
        from veil.environment.deployment import register_deployment_settings_provider
        from .setting import POSTGRESQL_BASE_SETTINGS

        register_deployment_settings_provider(lambda settings: POSTGRESQL_BASE_SETTINGS, 'base')