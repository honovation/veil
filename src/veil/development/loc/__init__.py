import veil_component

with veil_component.init_component(__name__):
    def init():
        from veil.development.self_checker import register_self_checker
        from .loc_checker import check_loc

        register_self_checker('loc', check_loc)