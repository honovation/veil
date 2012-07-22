######## export begin
from .database import register_database
from .database import require_current_database_schema_being
from .database import peek_databases

__all__ = [
    # from database
    register_database.__name__,
    require_current_database_schema_being.__name__,
    peek_databases.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()