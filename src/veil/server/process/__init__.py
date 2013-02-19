import veil_component

with veil_component.init_component(__name__):
    from .process_event import EVENT_PROCESS_SETUP
    from .process_event import EVENT_PROCESS_TEARDOWN

    __all__ = [
        'EVENT_PROCESS_SETUP',
        'EVENT_PROCESS_TEARDOWN'
    ]
