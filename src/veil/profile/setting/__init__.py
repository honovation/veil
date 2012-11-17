import veil_component

with veil_component.init_component(__name__):
    from veil.environment import *
    from veil.backend.database.new_postgresql_setting import postgresql_program
