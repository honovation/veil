import veil_component

with veil_component.init_component(__name__):
    def init():
        from veil_installer import register_installer
        from .basic_layout_installer import  install_basic_layout

        register_installer('basic-layout', install_basic_layout)
