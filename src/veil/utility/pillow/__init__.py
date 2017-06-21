import veil_component

with veil_component.init_component(__name__):
    from pillow import open_image
    from pillow import save_image
    from pillow import crop_image
    from pillow import generate_thumbnail
    from pillow import generate_captcha_image_and_answer
    from pillow import InvalidImage
    from pillow import get_wqy_font

    __all__ = [
        # from pillow
        open_image.__name__,
        save_image.__name__,
        crop_image.__name__,
        generate_thumbnail.__name__,
        generate_captcha_image_and_answer.__name__,
        InvalidImage.__name__,
        get_wqy_font.__name__,
    ]
