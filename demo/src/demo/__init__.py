import veil.component

with veil.component.init_component(__name__):
    def init():
        from veil.environment.setting import add_settings
        from .setting import demo_settings

        add_settings(demo_settings())