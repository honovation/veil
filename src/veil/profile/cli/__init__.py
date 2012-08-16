import sandal.component

with sandal.component.init_component(__name__):
    from veil.frontend.cli import *
    from veil.backend.shell import *
    from veil.environment.setting import *