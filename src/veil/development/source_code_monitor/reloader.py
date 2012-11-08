from __future__ import unicode_literals, print_function, division
import threading
import functools
from veil.environment.supervisor import *

death_list = set()

def register_reloads_on_change_group(group):
    death_list.add('{}:'.format(group))


def register_reloads_on_change_program(program):
    death_list.add(program)


def restart_all():
    execute('restart')


def start_all():
    execute('start')


def execute(action):
    threads = []
    for death_target in death_list:
        killer = functools.partial(supervisorctl, action, death_target)
        thread = threading.Thread(target=killer)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()