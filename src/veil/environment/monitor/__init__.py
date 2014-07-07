import veil_component

with veil_component.init_component(__name__):
    from .elk import logstash_resource
    from .elk import elasticsearch_resource
    from .elk import kibana_resource
    from .elk import oracle_java_resource

    __all__ = [
        logstash_resource.__name__,
        elasticsearch_resource.__name__,
        kibana_resource.__name__,
        oracle_java_resource.__name__,
    ]