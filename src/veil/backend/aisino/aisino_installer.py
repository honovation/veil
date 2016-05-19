# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import *
from veil.server.config import *
from veil.server.os import *
from veil.utility.setting import *
from veil_installer import *

_config = None

add_application_sub_resource('aisino_invoice', lambda config: aisino_invoice_resource(**config))


@composite_installer
def aisino_invoice_resource(payer_id, payer_name, payer_auth_code, payer_address, payer_telephone, payer_bank_account_no, ebp_code, registration_no,
                            operator_name):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'aision_invoice.cfg', content=render_config('aision_invoice.cfg.j2',
                                                                                                   payer_id=payer_id,
                                                                                                   payer_name=payer_name,
                                                                                                   payer_auth_code=payer_auth_code,
                                                                                                   payer_address=payer_address,
                                                                                                   payer_telephone=payer_telephone,
                                                                                                   payer_bank_account_no=payer_bank_account_no,
                                                                                                   ebp_code=ebp_code,
                                                                                                   registration_no=registration_no,
                                                                                                   operator_name=operator_name)))
    return resources


def load_aisino_invoice_config():
    return load_config_from(VEIL_ETC_DIR / 'aision_invoice.cfg', 'payer_id', 'payer_name', 'payer_auth_code', 'payer_address', 'payer_telephone',
                            'payer_bank_account_no', 'ebp_code', 'registration_no', 'operator_name')


def aisino_invoice_config():
    global _config
    if _config is None:
        _config = load_aisino_invoice_config()
    return _config
