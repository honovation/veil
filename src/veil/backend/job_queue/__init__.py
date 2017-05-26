# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import veil_component
from veil_installer import add_application_sub_resource
from .queue_client_installer import queue_client_resource

with veil_component.init_component(__name__):

    from .job_queue import task

    __all__ = [
        task.__name__,
    ]

    def init():
        add_application_sub_resource('queue_client', lambda config: queue_client_resource(**config))
