import veil_component

with veil_component.init_component(__name__):

    from .aisino import request_invoice
    from .aisino import download_invoice
    from .aisino import as_request_seq
    from .aisino import query_invoice
    from .aisino import INVOICE_INTERFACE_NAME_FOR_INVOICE
    from .aisino import INVOICE_INTERFACE_NAME_FOR_DOWNLOAD
    from .aisino import INVOICE_APP_ID_NORMAL
    from .aisino import INVOICE_APP_ID_VAT
    from .aisino import INVOICE_TYPE_CODE_NORMAL
    from .aisino import INVOICE_TYPE_CODE_RED
    from .aisino import INVOICE_BUYER_TYPE_COMPANY
    from .aisino import INVOICE_BUYER_TYPE_GOV
    from .aisino import INVOICE_BUYER_TYPE_PERSONAL
    from .aisino import INVOICE_BUYER_TYPE_OTHER
    from .aisino import INVOICE_ITEM_TYPE_NORMAL
    from .aisino import INVOICE_ITEM_TYPE_DISCOUNT
    from .aisino import INVOICE_ITEM_TYPE_BE_DISCOUNTED
    from .aisino import INVOICE_OPERATION_CODE_NORMAL
    from .aisino import INVOICE_OPERATION_CODE_REVERT_NORMAL
    from .aisino import INVOICE_OPERATION_CODE_RETURN_RED
    from .aisino import INVOICE_OPERATION_CODE_REVERT_RED
    from .aisino import INVOICE_OPERATION_CODE_REPLACE_RED
    from .aisino import InvoiceTaxPayer
    from .aisino import InvoiceBuyer
    from .aisino import InvoiceItem
    from .aisino import DEFAULT_TAX_RATE
    from .aisino import RED_INVOICE_FLAG_NORMAL
    from .aisino import RED_INVOICE_FLAG_SPECIAL

    from .aisino_installer import aisino_invoice_resource
    from .aisino_installer import aisino_invoice_config

    __all__ = [
        request_invoice.__name__,
        download_invoice.__name__,
        as_request_seq.__name__,
        query_invoice.__name__,
        'INVOICE_INTERFACE_NAME_FOR_INVOICE',
        'INVOICE_INTERFACE_NAME_FOR_DOWNLOAD',
        'INVOICE_APP_ID_NORMAL',
        'INVOICE_APP_ID_VAT',
        'INVOICE_TYPE_CODE_NORMAL',
        'INVOICE_TYPE_CODE_RED',
        'INVOICE_BUYER_TYPE_COMPANY',
        'INVOICE_BUYER_TYPE_GOV',
        'INVOICE_BUYER_TYPE_PERSONAL',
        'INVOICE_BUYER_TYPE_OTHER',
        'INVOICE_ITEM_TYPE_NORMAL',
        'INVOICE_ITEM_TYPE_DISCOUNT',
        'INVOICE_ITEM_TYPE_BE_DISCOUNTED',
        'INVOICE_OPERATION_CODE_NORMAL',
        'INVOICE_OPERATION_CODE_REVERT_NORMAL',
        'INVOICE_OPERATION_CODE_RETURN_RED',
        'INVOICE_OPERATION_CODE_REVERT_RED',
        'INVOICE_OPERATION_CODE_REPLACE_RED',
        InvoiceTaxPayer.__name__,
        InvoiceBuyer.__name__,
        InvoiceItem.__name__,
        'DEFAULT_TAX_RATE',
        'RED_INVOICE_FLAG_NORMAL',
        'RED_INVOICE_FLAG_SPECIAL',

        aisino_invoice_resource.__name__,
        aisino_invoice_config.__name__,
    ]
