import logging
import shlex
import os

LOGGER = logging.getLogger(__name__)


def pass_control_to(command_line):
    command_args = shlex.split(command_line)
    os.execlp(command_args[0], *command_args)