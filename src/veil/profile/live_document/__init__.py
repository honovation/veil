import veil_component

with veil_component.init_component(__name__):
    from veil.development.test import get_fixture as g
    from veil.development.live_document import execute_document_statement as i
    from veil.development.live_document import verify as v
    from veil.development.live_document import pause