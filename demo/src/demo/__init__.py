def init():
    from sandal.component import init_component
    from sandal.const import consts
    from sandal.event import subscribe_event
    from sandal.option import init_options
    from sandal.option import merge_options

    init_component(__name__)

    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    subscribe_event(consts.EVENT_ENVIRONMENT_INSTALLING, lambda options: init_options(merge_options(options, {
        'websites': {
            'demo': {
                'server_name': 'demo.dev.dmright.com',
                'host': DEMO_WEB_HOST,
                'port': DEMO_WEB_PORT
            }
        }
    })))

init()