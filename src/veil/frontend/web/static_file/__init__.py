import veil.component

with veil.component.init_component(__name__):
    from .static_file import clear_static_file_hashes

    __all__ = [
        clear_static_file_hashes.__name__
    ]

    def init():
        from .static_file import process_javascript_and_stylesheet_tags
        from veil.frontend.template import register_page_post_processor

        register_page_post_processor(process_javascript_and_stylesheet_tags)