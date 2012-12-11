import veil_component

with veil_component.init_component(__name__):
    from .source_code_monitor import source_code_monitored

    __all__ = [
        source_code_monitored.__name__
    ]