import veil_component

with veil_component.init_component(__name__):
    from .remote_deployer import veil_env_in_service_resource

    __all__ = [
        veil_env_in_service_resource.__name__
    ]