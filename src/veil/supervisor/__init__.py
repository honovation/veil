import sandal.component

with sandal.component.init_component(__name__):
    def init():
        from veil.environment.setting import register_settings_provider
        from .setting import SUPERVISOR_BASE_SETTINGS

        register_settings_provider(lambda settings: SUPERVISOR_BASE_SETTINGS, 'base')