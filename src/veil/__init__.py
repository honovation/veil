import veil_component
import traceback

def init_components():
    component_names = [
        'veil.backend.bucket',
        'veil.backend.database.client',
        'veil.backend.database.postgresql',
        'veil.backend.database.db2',
        'veil.backend.queue',
        'veil.backend.redis',
        'veil.backend.shell',
        'veil.development.architecture',
        'veil.development.browser',
        'veil.development.git',
        'veil.development.loc',
        'veil.development.pycharm',
        'veil.development.test',
        'veil.environment.deployment',
        'veil.environment.installation',
        'veil.environment.source_code_monitor',
        'veil.environment.setting',
        'veil.environment.supervisor',
        'veil.frontend.cli',
        'veil.frontend.encoding',
        'veil.frontend.locale',
        'veil.frontend.template',
        'veil.frontend.web'
    ]
    try:
        from .environment import get_application_components
        for component_name in get_application_components():
            component_names.append(component_name)
    except:
        traceback.print_exc()
    for component_name in component_names:
        __import__(component_name)