# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from .sms import SMService

SMS_PROVIDER_ID = 2


def get_yunpian_smservice_instance():
    return YunpianSMService(SMS_PROVIDER_ID)


class YunpianSMService(SMService):
    def __init__(self, sms_provider_id):
        super(YunpianSMService, self).__init__(sms_provider_id)

    def get_receiver_list(self, receivers):
        if isinstance(receivers, basestring):
            receivers = [receivers]
        return

    def send(self, receivers, message, sms_code, transactional):
        print('send via yunpian')

    def query_balance(self):
        print('query balance via yunpian')
