import sandal.component
init_components = lambda : sandal.component.init_components([
    'veil.frontend.template',
    'veil.frontend.web.nginx',
    'veil.backend.queue',
    'veil.backend.database',
    'veil.backend.redis',
    'veil.environment.runtime',
    'veil.environment.deployment',
    'veil.development',
    'veil.supervisor',
    '__veil__'
])