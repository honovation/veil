from veil_installer import *

import veil_component
with veil_component.init_component(__name__):

    from .qcloud_ocr_installer import qcloud_ocr_client_resource

    from .qcloud_ocr import get_ocr_result
    from .qcloud_ocr import ImageOCRException

    def init():
        add_application_sub_resource('qcloud_ocr_client', lambda config: qcloud_ocr_client_resource(**config))

    __all__ = [
        qcloud_ocr_client_resource.__name__,

        get_ocr_result.__name__,
        ImageOCRException.__name__,
    ]
