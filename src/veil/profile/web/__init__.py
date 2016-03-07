import veil_component

with veil_component.init_component(__name__):
    import httplib
    from veil.frontend.template import *
    from veil.model.command import *
    from veil.model.security import *
    from veil.frontend.web import *
    from veil.frontend.visitor import *
