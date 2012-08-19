import veil.component
init_components = lambda : veil.component.init_components([
    'veil.frontend.template',
    'veil.frontend.web.nginx',
    'veil.backend.database',
    'veil.backend.redis',
    'veil.environment.setting',
    'veil.environment.setting',
    'veil.development.browser',
    'veil.development.pycharm',
    'veil.development.test',
    'veil.supervisor',
    '__veil__'
])