from .environment import get_application_components
from .environment import VEIL_SERVER

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
        'veil.development.source_code_monitor',
        'veil.environment.deployment',
        'veil.environment.setting',
        'veil.environment.supervisor',
        'veil.frontend.cli',
        'veil.frontend.encoding',
        'veil.frontend.locale',
        'veil.frontend.template',
        'veil.frontend.nginx',
        'veil.frontend.web'
    ]
    component_names.extend(get_application_components())
    for component_name in component_names:
        try:
            __import__(component_name)
        except:
            if 'development' == VEIL_SERVER:
                raise
            pass # try our best to import as many components as possible
