import veil.component

with veil.component.init_component(__name__):
    from .static_file import clear_static_file_hashes
    from .static_file import set_inline_static_files_directory
    from .static_file import set_external_static_files_directory
    from .static_file import open_closed_tags

    __all__ = [
        clear_static_file_hashes.__name__,
        set_inline_static_files_directory.__name__,
        set_external_static_files_directory.__name__,
        open_closed_tags.__name__
    ]

    def init():
        from .static_file import process_javascript_and_stylesheet_tags
        from veil.frontend.template import register_page_post_processor

        register_page_post_processor(process_javascript_and_stylesheet_tags)