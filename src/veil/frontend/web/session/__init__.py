import veil.component

with veil.component.init_component(__name__):
    from .session import register_website_session

    __all__ = [
        register_website_session.__name__
    ]