import veil_component

with veil_component.init_component(__name__):

    from .elasticsearch_installer import elasticsearch_resource
    from .kibana_installer import kibana_resource
    from .logstash_installer import logstash_resource
    from .logstash_installer import oracle_java_resource

    __all__ = [
        elasticsearch_resource.__name__,
        kibana_resource.__name__,
        logstash_resource.__name__,
        oracle_java_resource.__name__,
    ]