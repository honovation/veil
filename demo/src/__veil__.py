demo = __import__('demo')

ARCHITECTURE = {
    'demo.model.item': [
        'veil.backend.redis', 'veil.model', 'veil.profile.model',
        'veil.backend.database', 'veil.utility.clock']
}