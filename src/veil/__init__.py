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
    'veil.environment.setting',
    'veil.environment.installation',
    'veil.frontend.cli',
    'veil.frontend.encoding',
    'veil.frontend.locale',
    'veil.frontend.template',
    'veil.frontend.web',
    'veil.supervisor'
])
try:
    __import__('__veil__')
except:
    traceback.print_exc()