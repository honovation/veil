import veil_component

with veil_component.init_component(__name__):
    from .widget import widget
    from .widget import require_current_widget_namespace_being
    from .widget import import_widget

    __all__ = [
        # from widget
        widget.__name__,
        require_current_widget_namespace_being.__name__,
        import_widget.__name__
    ]