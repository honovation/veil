import veil_component

with veil_component.init_component(__name__):
    def init():
        from veil_installer import register_installer
        from .pg_server_installer import install_postgresql_server

        register_installer('postgresql', install_postgresql_server)
