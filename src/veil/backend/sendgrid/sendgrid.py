# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import smtplib
import logging
from email.utils import parseaddr, formataddr
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from veil_component import VEIL_ENV_TYPE
from veil.environment import get_application_email_whitelist
from veil.backend.queue import *
from veil.development.test import *
from veil.model.event import *
from veil.server.process import *
from .sendgrid_client_installer import sendgrid_client_config

LOGGER = logging.getLogger(__name__)

smtp = None


@event(EVENT_PROCESS_TEARDOWN)
def close_connection():
    if smtp is not None:
        try:
            smtp.quit()
        except smtplib.SMTPServerDisconnected:
            pass
        except Exception:
            LOGGER.exception('failed to quit smtp')


def open_connection():
    global smtp
    smtp = smtplib.SMTP('smtp.sendgrid.net', port=587, timeout=120)
    config = sendgrid_client_config()
    smtp.login(config.username, config.password)


def is_connected():
    if smtp is None:
        return False
    try:
        status = smtp.noop()[0]
    except Exception:   # smtplib.SMTPServerDisconnected
        status = -1
    return status == 250


def reconnect_if_broken_per_verification():
    if not is_connected():
        close_connection()
        open_connection()


@mockable
def send_email(sender, recipient, subject, text='', html='', category='', email_code=''):
    sender_name, sender_addr = parseaddr(sender)
    from_addr = formataddr((Header(sender_name, 'UTF-8').encode(), sender_addr))
    recipient_name, recipient_addr = parseaddr(recipient)
    if 'public' != VEIL_ENV_TYPE and recipient_addr not in get_application_email_whitelist():
        LOGGER.warn('Ignored email address not in the whitelist under non-public env: %(recipient_addr)s', {'recipient_addr': recipient_addr})
        return
    to_addr = formataddr((Header(recipient_name, 'UTF-8').encode(), recipient_addr))

    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    if category:
        msg["X-SMTPAPI"] = '{{"category" : "{}"}}'.format(category)
    if text:
        text_part = MIMEText(text, 'plain', 'UTF-8')
        msg.attach(text_part)
    if html:
        html_part = MIMEText(html, 'html', 'UTF-8')
        msg.attach(html_part)
    try:
        reconnect_if_broken_per_verification()
        smtp.sendmail(from_addr, to_addr, msg.as_string())
    except Exception:
        LOGGER.exception('failed to send email: %(email_code)s, %(to_addr)s', {
            'email_code': email_code,
            'to_addr': to_addr
        })
        raise
    else:
        LOGGER.info('succeeded to send email: %(email_code)s, %(to_addr)s', {
            'email_code': email_code,
            'to_addr': to_addr
        })


@job('send_transactional_email', retry_every=3 * 60, retry_timeout=3 * 60 * 60)
def send_transactional_email_job(sender, recipient, subject, text='', html='', category='', email_code=''):
    send_email(sender, recipient, subject, text, html, category, email_code)
