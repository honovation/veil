import veil_component
with veil_component.init_component(__name__):
    if veil_component.VEIL_ENV.is_test:
        from .selenium_installer import selenium_python_package_resource
    else:
        def do_nothing(*args, **kwargs):
            pass
        selenium_python_package_resource = do_nothing

    __all__ = [
        selenium_python_package_resource.__name__,
    ]
