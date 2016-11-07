import veil_component

with veil_component.init_component(__name__):
    if veil_component.VEIL_ENV.is_test:
        from .chrome_driver_installer import chrome_driver_resource
        from .selenium_installer import selenium_python_package_resource
    else:
        def do_nothing(*args, **kwargs):
            pass
        chrome_driver_resource = do_nothing
        selenium_python_package_resource = do_nothing

    __all__ = [
        chrome_driver_resource.__name__,
        selenium_python_package_resource.__name__,
    ]
