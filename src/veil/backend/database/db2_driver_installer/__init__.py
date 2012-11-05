import veil_component

with veil_component.init_component(__name__):
    def init():
        from veil_installer import register_installer
        from .db2_driver_installer import install_db2_driver

        register_installer('db2-driver', install_db2_driver)
