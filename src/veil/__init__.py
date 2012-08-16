import sandal.component
init_components = lambda : sandal.component.init_components([
    'veil.frontend.template',
    'veil.frontend.web.nginx',
    'veil.backend.queue',
    'veil.backend.database',
    'veil.backend.redis',
    'veil.environment.setting',
    'veil.environment.setting',
    'veil.development',
    'veil.supervisor',
    '__veil__'
])