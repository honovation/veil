from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.server.os import *
from veil.server.supervisor import *


@composite_installer
def veil_server_resource():
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        basic_layout_resources = [
                directory_resource(path=VEIL_ENV_DIR),
                directory_resource(path=VEIL_ETC_DIR.parent),
                directory_resource(path=VEIL_ETC_DIR),
                directory_resource(path=VEIL_LOG_DIR.parent),
                directory_resource(path=VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
                directory_resource(path=VEIL_VAR_DIR),
                directory_resource(path=VEIL_BUCKETS_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
                directory_resource(path=VEIL_BUCKET_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
                directory_resource(path=VEIL_DATA_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
                directory_resource(path=VEIL_BARMAN_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
            ]
    elif VEIL_ENV.name != VEIL_ENV.base_name:
        basic_layout_resources = [symbolic_link_resource(path=VEIL_ENV_DIR.parent / VEIL_ENV.name, to=VEIL_ENV_DIR)]
    else:
        basic_layout_resources = []

    resources = list(basic_layout_resources)
    server = get_current_veil_server()
    if server.programs:
        resources.append(supervisor_resource(programs=to_supervisor_programs(server.programs),
                                             inet_http_server_host=server.supervisor_http_host,
                                             inet_http_server_port=server.supervisor_http_port,
                                             program_groups=to_supervisor_program_groups(server.programs)))
        for program in server.programs.values():
            resources.extend(program.get('resources', []))
    resources.extend(server.get('resources', []))
    return resources


def to_supervisor_programs(veil_server_programs):
    supervisor_programs = {}
    for program_name, veil_server_program in veil_server_programs.items():
        supervisor_program = {
            'execute_command': veil_server_program.execute_command,
            'run_as': veil_server_program.get('run_as', CURRENT_USER),
            'redirect_stderr': veil_server_program.get('redirect_stderr', True)
        }
        if 'run_in_directory' in veil_server_program:
            supervisor_program['run_in_directory'] = veil_server_program.run_in_directory
        if 'priority' in veil_server_program:
            supervisor_program['priority'] = veil_server_program.priority
        if 'environment_variables' in veil_server_program:
            supervisor_program['environment_variables'] = format_environment_variables(veil_server_program.environment_variables)
        if 'startsecs' in veil_server_program:
            supervisor_program['startsecs'] = veil_server_program.startsecs
        if 'startretries' in veil_server_program:
            supervisor_program['startretries'] = veil_server_program.startretries
        if 'stopwaitsecs' in veil_server_program:
            supervisor_program['stopwaitsecs'] = veil_server_program.stopwaitsecs
        if 'stopsignal' in veil_server_program:
            supervisor_program['stopsignal'] = veil_server_program.stopsignal
        supervisor_programs[program_name] = supervisor_program
    return supervisor_programs


def to_supervisor_program_groups(veil_server_programs):
    supervisor_program_groups = {}
    for program_name, veil_server_program in veil_server_programs.items():
        program_group_name = veil_server_program.get('group')
        if program_group_name:
            supervisor_program_groups.setdefault(program_group_name, set()).add(program_name)
    return supervisor_program_groups


def format_environment_variables(environment_variables):
    return ','.join('{}="{}"'.format(k, v) for k, v in environment_variables.items())
