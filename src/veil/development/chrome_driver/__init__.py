import veil_component

with veil_component.init_component(__name__):
    from .chrome_driver_installer import chrome_driver_resource

    __all__ = [
        chrome_driver_resource.__name__
    ]