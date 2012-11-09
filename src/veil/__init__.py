from .environment import get_application_components
from .environment import VEIL_SERVER

initialized = False

def init_components():
    global initialized
    if initialized:
        return
    initialized = True
    component_names = [
        'veil.backend.bucket',
        'veil.backend.database.client',
        'veil.backend.database.postgresql',
        'veil.backend.database.db2',
        'veil.backend.queue',
        'veil.backend.redis',
        'veil.backend.shell',
        'veil.development.architecture',
        'veil.development.git',
        'veil.development.loc',
        'veil.development.pycharm',
        'veil.development.test',
        'veil.development.source_code_monitor',
        'veil.environment.local_deployer',
        'veil.environment.remote_deployer',
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
            if VEIL_SERVER in ['development', 'test']:
                raise
            pass # try our best to import as many components as possible
    __import__('__veil__')