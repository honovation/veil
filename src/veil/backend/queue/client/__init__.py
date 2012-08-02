import sandal.component

with sandal.component.init_component(__name__):
    from .queue import require_queue

    __all__ = [
        # from queue
        require_queue.__name__
    ]