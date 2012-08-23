import veil.component

with veil.component.init_component(__name__):
    import httplib
    from veil.frontend.template import *
    from veil.model.command import *
    from veil.frontend.web.launcher import *
    from veil.frontend.web.routing import *
    from veil.frontend.web.tornado import *
