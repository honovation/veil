import veil.component
import traceback

init_components = lambda : veil.component.init_components([
    'veil.frontend.template',
    'veil.frontend.locale',
    'veil.frontend.web.nginx',
    'veil.backend.database.client',
    'veil.backend.database.postgresql',
    'veil.backend.database.db2',
    'veil.backend.redis',
    'veil.backend.bucket',
    'veil.environment.installation',
    'veil.environment.setting',
    'veil.development.browser',
    'veil.development.pycharm',
    'veil.development.test',
    'veil.development.git',
    'veil.supervisor'
])
try:
    __import__('__veil__')
except:
    traceback.print_exc()