import importlib

COMPONENTS = [
    importlib.import_module('demo.model.item'),
    importlib.import_module('demo.model.audit_log'),
    importlib.import_module('demo.website.demo')
]

ARCHITECTURE = {
    'demo.model.item': [
        'veil.backend.redis', 'veil.model', 'veil.profile.model',
        'veil.backend.database', 'veil.utility.clock']
}