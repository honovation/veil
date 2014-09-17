# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

WEB_SPIDER_NAMES = (
    b'Baiduspider', b'360Spider', b'qihoobot', b'Sogou web spider', b'Sogou Pic spider', b'Sogou inst spider', b'Googlebot', b'bingbot',
    b'BingPreview', b'msnbot', b'EtaoSpider', b'Sosospider', b'YoudaoBot', b'YoudaoGouwuBot', b'Yahoo! Slurp', b'ia_archiver', b'magpie-crawler',
    b'MJ12bot', b'heritrix', b'JikeSpider',
)

def is_web_spider(user_agent):
    return user_agent and any(spider_name in user_agent for spider_name in WEB_SPIDER_NAMES)
