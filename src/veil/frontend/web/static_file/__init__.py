import veil_component

with veil_component.init_component(__name__):
    from .static_file import clear_static_file_hashes
    from .static_file import process_javascript
    from .static_file import process_stylesheet
    from .static_file import set_external_static_files_directory
    from .static_file import static_url
    from .script_element import process_script_elements

    __all__ = [
        clear_static_file_hashes.__name__,
        process_javascript.__name__,
        process_stylesheet.__name__,
        set_external_static_files_directory.__name__,
        static_url.__name__,
        process_script_elements.__name__
    ]
