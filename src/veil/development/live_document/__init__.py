import veil_component

with veil_component.init_component(__name__):
    from .live_document import execute_document_statement
    from .live_document import document_statement
    from .browser import open_browser_page
    from .verification import verify
    from .break_point import pause

    __all__ = [
        execute_document_statement.__name__,
        document_statement.__name__,
        open_browser_page.__name__,
        verify.__name__,
        pause.__name__
    ]

    def init():
        from veil.development.self_checker import register_self_checker
        from .live_document_checker import check_live_document

        register_self_checker('live-document', check_live_document)
