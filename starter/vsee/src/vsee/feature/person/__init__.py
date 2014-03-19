from __future__ import unicode_literals, print_function, division
import veil_component

with veil_component.init_component(__name__):
    from .person import list_persons

    __all__=[
        list_persons.__name__,
    ]