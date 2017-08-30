import veil_component
with veil_component.init_component(__name__):

    from .xml import parse_xml

    __all__ = [
        parse_xml.__name__,
    ]
