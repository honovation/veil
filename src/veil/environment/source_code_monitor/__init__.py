import veil.component

with veil.component.init_component(__name__):
    from .reloader import register_reloads_on_change_group
    from .reloader import register_reloads_on_change_program

    __all__ = [
        register_reloads_on_change_group.__name__,
        register_reloads_on_change_program.__name__
    ]

    def init():
        from veil.environment.setting import add_settings
        from .source_code_monitor import source_code_monitor_settings

        add_settings(source_code_monitor_settings())