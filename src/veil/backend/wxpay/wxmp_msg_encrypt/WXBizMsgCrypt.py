# -*- coding: utf-8 -*-
""" 对公众平台发送给公众账号的消息加解密示例代码.
@copyright: Copyright (c) 1998-2014 Tencent Inc.
"""
from __future__ import unicode_literals, print_function, division
import logging
import base64
import string
import random
import hashlib
import time
import struct
from Crypto.Cipher import AES
import socket
import lxml
import ierror
from veil.model.collection import DictObject

LOGGER = logging.getLogger(__name__)

SUPPORT_ENCRYPT_METHODS = {'aes'}
KEY_LENGTH = 32
AES_TEXT_RESPONSE_TEMPLATE = '<xml><Encrypt><![CDATA[%(encrypt)s]]></Encrypt><MsgSignature><![CDATA[%(signature)s]]></MsgSignature><TimeStamp>%(timestamp)s</TimeStamp><Nonce><![CDATA[%(nonce)s]]></Nonce></xml>'
TEXT_RESPONSE_TEMPLATE = '<xml><ToUserName><![CDATA[%(to_user)s]]></ToUserName><FromUserName><![CDATA[%(from_user)s]]></FromUserName><CreateTime>%(timestamp)s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%(content)s]]></Content></xml>'


def sign_wxmp_params(*args):
    args_ = [e for e in args]
    args_.sort()
    sha = hashlib.sha1()
    sha.update(''.join(args_))
    return sha.hexdigest().lower()


def parse_xml(xmltext):
    arguments = DictObject()
    root = lxml.objectify.fromstring(xmltext)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments


def render_wxmp_text_encrypted_response(encrypt, signature, timestamp, nonce):
    resp_dict = {'encrypt': encrypt, 'signature': signature, 'timestamp': timestamp, 'nonce': nonce}
    resp_xml = AES_TEXT_RESPONSE_TEMPLATE % resp_dict
    return resp_xml


def render_wxmp_text_response(to_user, from_user, timestamp, content):
    return TEXT_RESPONSE_TEMPLATE % {'to_user': to_user, 'from_user': from_user, 'timestamp': timestamp, 'content': content}


def padding_to_pkcs7(text):
    # 计算需要填充的位数
    amount_to_padding = KEY_LENGTH - (len(text) % KEY_LENGTH)
    if amount_to_padding == 0:
        amount_to_padding = KEY_LENGTH
    # 获得补位所用的字符
    pad = chr(amount_to_padding)
    return text + pad * amount_to_padding


def remove_pkcs7_padding(decrypted_text):
    pad = ord(decrypted_text[-1])
    if pad < 1 or pad > 32:
        pad = 0
    return decrypted_text[:-pad]


class Prpcrypt(object):
    def __init__(self, key):
        self.key = key
        # 设置加解密模式为AES的CBC模式
        self.mode = AES.MODE_CBC

    def encrypt(self, text, app_id):
        # 16位随机字符串添加到明文开头
        text = self.get_random_str() + struct.pack('I', socket.htonl(len(text))) + text + app_id
        # 使用自定义的填充方式对明文进行补位填充
        text = padding_to_pkcs7(text)
        # 加密
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        try:
            ciphertext = cryptor.encrypt(text)
            # 使用BASE64对加密后的字符串进行编码
            return ierror.WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception as e:
            LOGGER.warn('encrypt failed: %(error)s', {
                'error': e.message
            })
            return ierror.WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text, app_id):
        try:
            cryptor = AES.new(self.key, self.mode, self.key[:16])
            plain_text = cryptor.decrypt(base64.b64decode(text))
        except Exception as e:
            LOGGER.warn('decrypt failed: %(error)s', {
                'error': e.message
            })
            return ierror.WXBizMsgCrypt_DecryptAES_Error, None
        try:
            pad = ord(plain_text[-1])
            # 去除16位随机字符串
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4:xml_len+4]
            from_appid = content[xml_len+4:]
        except Exception as e:
            LOGGER.warn('extract data from decrypt failed: %(error)s', {
                'error': e.message
            })
            return ierror.WXBizMsgCrypt_IllegalBuffer, None
        if from_appid != app_id:
            return ierror.WXBizMsgCrypt_ValidateAppid_Error, None
        return xml_content

    @staticmethod
    def get_random_str():
        rule = string.letters + string.digits
        return ''.join(random.sample(rule, 16))


class WXBizMsgCrypt(object):
    def __init__(self, token, encoding_aes_key, app_id):
        try:
            self.key = base64.b64decode(encoding_aes_key + '=')
            assert len(self.key) == 32
        except Exception:
            LOGGER.warn('encoding aes key is invalid format')
            raise
        self.token = token
        self.app_id = app_id

    def encrypt_msg(self, msg, nonce, timestamp=None):
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(msg, self.app_id)
        if timestamp is None:
            timestamp = str(int(time.time()))
        signature = sign_wxmp_params(self.token, timestamp, nonce, encrypt)
        return render_wxmp_text_encrypted_response(encrypt, signature, timestamp, nonce)

    def decrypt_msg(self, msg, msg_signature, timestamp, nonce):
        try:
            parsed_msg = parse_xml(msg)
        except Exception as e:
            raise Exception('bad xml format: {}'.format(e.message))
        signature = sign_wxmp_params(self.token, timestamp, nonce, parsed_msg.Encrypt)
        if signature != msg_signature:
            LOGGER.warn('signature mismatch: %(expected_sign)s, %(actual_sign)s', {'expected_sign': signature, 'actual_sign': msg_signature})
            raise Exception('signature mismatch')
        pc = Prpcrypt(self.key)
        xml_content = pc.decrypt(parsed_msg.Encrypt, self.app_id)
        return parse_wechat_plain_msg(xml_content)


def parse_wechat_plain_msg(xml):
    return parse_xml(xml)
