from .environment import get_application_components

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
    component_names.extend(get_application_components())
    for component_name in component_names:
        try:
            __import__(component_name)
        except:
            pass # try our best to import as many components as possible
