import veil.component
import traceback

init_components = lambda : veil.component.init_components([
    'veil.backend.bucket',
    'veil.backend.database.client',
    'veil.backend.database.postgresql',
    'veil.backend.database.db2',
    'veil.backend.queue',
    'veil.backend.redis',
    'veil.backend.shell',
    'veil.development.browser',
    'veil.development.git',
    'veil.development.pycharm',
    'veil.development.test',
    'veil.environment.deployment',
    'veil.environment.installation',
    'veil.environment.setting',
    'veil.frontend.cli',
    'veil.frontend.encoding',
    'veil.frontend.locale',
    'veil.frontend.template',
    'veil.frontend.web',
    'veil.supervisor'
])
try:
    import __veil__
    for component_name in __veil__.COMPONENTS:
        __import__(component_name)
except:
    traceback.print_exc()