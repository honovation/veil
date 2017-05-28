# -*- coding: utf-8 -*-
"""
One single certificate for multiple domains is not supported

How to use letsencrypt certificate for a website under a domain
1. update veil app env config to add the parent domain under base_domain_names and deploy
2. ssh to veil server hosting nginx service
3. install/upgrade certbot: sudo veil :ljmall-public--2/web server certbot install
4. get the certificate for the domain: sudo veil :ljmall-public--2/web server certbot certonly www.lijiababy.com.cn
5. update veil app env config to add the website with use_certbot=True
6. deploy and verify

How to renew letsencrypt certificates
1. ssh to veil server hosting nginx service
2. renew letsencrypt certificates and reload nginx if necessary: sudo veil :ljmall-public--2/web server certbot renew

When switching nginx service to another veil server, need copy /etc/letsencrypt/ to the new veil server
"""
from __future__ import unicode_literals, print_function, division

from veil.frontend.cli import *
from veil.utility.shell import *
from veil.utility.timer import *
from veil.environment import get_application


@script('install')
def install():
    shell_execute('add-apt-repository ppa:certbot/certbot -y -u', capture=True)
    shell_execute('apt -y install certbot', capture=True)


@script('certonly')
def certonly(domain_name, staging=False):
    staging_option = '--staging' if staging == 'TRUE' else ''
    email = get_application().CERTBOT_EMAIL
    cmd = 'certbot certonly {} --non-interactive --no-eff-email --agree-tos --email {} --keep-until-expiring ' \
          '--allow-subset-of-names --expand --renew-with-new-domains --rsa-key-size 2048 --webroot -w /var/www/html/ ' \
          '-d {}'.format(staging_option, email, domain_name)
    shell_execute(cmd, capture=True)


@script('renew')
def renew():
    shell_execute('certbot renew --rsa-key-size 2048 --post-hook "veil server supervisor reload-nginx"', capture=True)


@script('renew-termly')
def renew_termly(crontab_expression):
    @run_every(crontab_expression)
    def work():
        renew()

    work()
