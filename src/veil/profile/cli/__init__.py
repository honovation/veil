import veil_component

with veil_component.init_component(__name__):
    from veil.frontend.cli import *
    from veil.backend.shell import *
    from veil.backend.database.client import *
    from veil.environment.setting import *