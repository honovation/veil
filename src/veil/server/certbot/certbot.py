# -*- coding: utf-8 -*-
"""
One single certificate for multiple domains is not supported

How to use letsencrypt certificate for a website under a domain
1. update veil app env config to add the parent domain under base_domain_names and deploy
2. ssh to veil server hosting nginx service
3. install/upgrade certbot: sudo veil server certbot install
4. get the certificate for the domain: sudo veil server certbot certonly www.lijiababy.com.cn
5. update veil app env config to add the website with use_certbot=True
6. deploy and verify

How to renew letsencrypt certificates
1. ssh to veil server hosting nginx service
2. renew letsencrypt certificates and reload nginx if necessary: sudo veil server certbot renew

When switching nginx service to another veil server, need copy /etc/letsencrypt/ to the new veil server
"""
from __future__ import unicode_literals, print_function, division

from veil.frontend.cli import *
from veil.utility.shell import *
from veil.utility.timer import *
from veil.environment import get_application

RELOAD_NGINX_CMD = 'veil server supervisor reload-nginx'


@script('install')
def install():
    shell_execute('add-apt-repository ppa:certbot/certbot -y -u', capture=True)
    shell_execute('apt -y install certbot', capture=True)


@script('certonly')
def certonly(domain_name, staging=False):
    staging_option = '--staging' if staging else ''
    email = get_application().CERTBOT_EMAIL
    cmd = 'certbot certonly {} --non-interactive --no-eff-email --agree-tos --email {} --keep-until-expiring ' \
          '--allow-subset-of-names --expand --renew-with-new-domains --rsa-key-size 4096 --must-staple --webroot ' \
          '-w /var/www/html/ -d {} --post-hook "{}"'.format(staging_option, email, domain_name, RELOAD_NGINX_CMD)
    shell_execute(cmd, capture=True)


@script('renew')
def renew():
    shell_execute('certbot renew --rsa-key-size 4096 --post-hook "{}"'.format(RELOAD_NGINX_CMD), capture=True)


@script('renew-termly')
def renew_termly(crontab_expression):
    @run_every(crontab_expression)
    def work():
        renew()

    work()
