from .environment import get_application_components
from .environment import VEIL_SERVER
from .environment.setting import bootstrap_runtime

initialized = False

def init_components(must_load_module_name=None):
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
            if must_load_module_name and must_load_module_name.startswith(component_name.replace('veil.', '')):
                raise
            pass # try our best to import as many components as possible
    __import__('__veil__')
    bootstrap_runtime()