import veil_component

with veil_component.init_component(__name__):

    from .convertor import convert_to_baidu_coord
    from .convertor import convert_baidu_coord_to_cgj02

    __all__ = [
        convert_to_baidu_coord.__name__,
        convert_baidu_coord_to_cgj02.__name__,
    ]
