import veil_component

with veil_component.init_component(__name__):

    from .convertor import convert_to_baidu_coord

    __all__ = [
        convert_to_baidu_coord.__name__,
    ]
