import veil.component

with veil.component.init_component(__name__):
    import httplib
    from veil.frontend.template import *
    from veil.model.command import *
    from veil.frontend.web.server import *
    from veil.frontend.web.tornado import *
