import veil_component

with veil_component.init_component(__name__):
    from .iptables_installer import iptables_rule_resource
    from .iptables_installer import iptables_rule_removed_resource
    from .iptables_installer import iptables_policy_resource

    __all__ = [
        # from iptables_installer
        iptables_rule_resource.__name__,
        iptables_rule_removed_resource.__name__,
        iptables_policy_resource.__name__
    ]